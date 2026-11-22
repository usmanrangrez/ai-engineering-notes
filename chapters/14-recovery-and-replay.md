## What it is and why it matters
A tracking service can fail after ticket preparation completed. Starting from scratch repeats work unnecessarily. A checkpointer can restore committed progress and schedule unfinished work.

## Learn from the beginning
**Prerequisite:** checkpoints and pending next nodes. Your goal is to explain exactly what is repeated after a failure and which external effects might happen twice.

### Concept 1 — Resume starts from saved execution state
**Recovery** is continuing useful work after a failure. Without saved state, rerunning the whole workflow may repeat completed operations. With checkpoints, the runtime can restore completed work and schedule pending work from the saved boundary.

```text
prepare [saved] --> tracking [fails] --> finish [not run]
                         |
service restored --> invoke(None, same thread)
                         |
                   tracking --> finish
```

`None` supplies no new input. It is not an instruction to delete state or to create an empty ticket. The selected checkpoint determines where execution continues. The tracking node restarts from its beginning; LangGraph is not resuming the HTTP request at the line where it failed.

### Concept 2 — The same method has three different starting situations
| Invocation | Starting point | Intended use |
| --- | --- | --- |
| `invoke(new_input, config=thread_config)` | Current thread plus new input update | New turn or new state contribution |
| `invoke(None, config=thread_config)` | Latest saved boundary | Continue pending work without new input |
| `invoke(None, config=old_snapshot.config)` | Explicit historical boundary | Replay from that earlier point |

**Replay** re-executes work after a historical checkpoint. Outputs can differ when models or external services are involved. If the latest checkpoint has no pending work, passing None does not invent a new user turn or force a finished node to run again. To pause/resume a human interrupt, a later chapter uses `Command(resume=...)`; do not substitute it into this failure-recovery example.

### Concept 3 — Saved state does not guarantee exactly-once side effects
A **side effect** changes something outside the graph's returned state: sending email, charging money, posting a job. A node may perform that action and then fail before its completion is durably recorded. Restarting it can perform the action again.

An **idempotent** operation is safe to repeat with the same logical request because its repeated application does not create an additional effect. Providers often support an **idempotency key**, a stable identifier used to deduplicate an operation. Designing side effects around durable identifiers and checkpoints is an engineering responsibility, not a benefit automatically obtained by adding a saver.

A successful sibling's pending writes can be saved even when another sibling fails in the same super-step. That helps recovery avoid rerunning completed sibling tasks. It does not mean arbitrary internal work halfway through a failing node is independently checkpointed.

## Build it in small pieces
The [offline recovery lab](../examples/14_recovery.py) raises a simulated tracking outage on the first invocation. It catches the error, reads saved state and next nodes, restores the service, then calls invoke(None). Count the prepare START lines and tracking START lines to prove the mechanism.

The failure switch lives outside graph state only as a local teaching simulation of an external service. It is not a robust production way to store retry status. A **retry** is another attempt at an operation; a **semantic revision** changes a candidate in response to quality feedback. They solve different problems.

## Check your understanding
Predict whether prepare or finish runs during the failed first attempt. After recovery, compare counts before accepting “resume works.”

::: question Exercise receipt: locate the boundary
Paste snapshot.next immediately after failure and the first START line after invoking None. The names should identify the pending work.
:::
::: question Exercise receipt: design for duplication
If prepare_ticket sent an email before failing, where would you place a stable operation ID and a deduplication check? Explain without sending anything.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/14_recovery.py). Run from the repository root:

```bash
uv run examples/14_recovery.py
```

::: question Complete runnable file — open after the small-step explanation
```python
"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from typing import TypedDict, NotRequired
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    ticket: str
    prepared: NotRequired[bool]
    tracking: NotRequired[str]
    resolution: NotRequired[str]

service = {"available": False}
counts = {"prepare": 0, "tracking": 0, "finish": 0}

def prepare(state):
    counts["prepare"] += 1
    log("prepare START")
    return {"prepared": True}

def tracking(state):
    counts["tracking"] += 1
    log(f"tracking START prepared={state['prepared']}")
    if not service["available"]:
        raise RuntimeError("Simulated tracking outage")
    return {"tracking": "IN_TRANSIT"}

def finish(state):
    counts["finish"] += 1
    log(f"finish START tracking={state['tracking']}")
    return {"resolution": "Ask the courier to investigate."}

builder = StateGraph(State)
for name, action in [("prepare", prepare), ("tracking", tracking), ("finish", finish)]:
    builder.add_node(name, action)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "tracking")
builder.add_edge("tracking", "finish")
builder.add_edge("finish", END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "recovery-demo"}}

if __name__ == "__main__":
    try:
        graph.invoke({"ticket": "My parcel is late."}, config=config)
    except RuntimeError as error:
        log(f"FAILED {error}")
    saved = graph.get_state(config)
    log(f"SAVED prepared={saved.values['prepared']} next={saved.next}")
    service["available"] = True
    log("RESUME")
    result = graph.invoke(None, config=config)
    assert counts == {"prepare": 1, "tracking": 2, "finish": 1}
    log(f"COUNTS {counts}")
    log(f"FINAL {result['resolution']}")
```
:::

Author verification output (elapsed times vary):

```text
[  0.23s] prepare START
[  0.23s] tracking START prepared=True
[  0.23s] FAILED Simulated tracking outage
[  0.23s] SAVED prepared=True next=('tracking',)
[  0.23s] RESUME
[  0.23s] tracking START prepared=True
[  0.23s] finish START tracking=IN_TRANSIT
[  0.23s] COUNTS {'prepare': 1, 'tracking': 2, 'finish': 1}
[  0.23s] FINAL Ask the courier to investigate.
```

| Trace observation | What it establishes |
| --- | --- |
| COUNTS has prepare=1, tracking=2, finish=1 | Recovery reused completed preparation and reran the failed node. |
| SAVED next contains tracking | The checkpoint identified exactly the unfinished work. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Preparation runs once, the failed tracking node runs twice, and finish runs once. invoke(None) adds no new input; it continues from the selected saved state. External side effects inside a repeated node need their own deduplication/idempotency design.
:::

## Historical learner lab record

## Lab: file 16
```bash
uv run 16_support_ticket_recovery.py
```
```text
▶ FIRST INVOCATION
prepare_ticket START
prepare_ticket DONE prepared=True
check_tracking START prepared=True
check_tracking FAILED simulated service outage
GRAPH STOPPED Simulated tracking service outage
SAVED STATE {'ticket': 'My parcel is late.', 'prepared': True}
NEXT NODES ('check_tracking',)
SERVICE RESTORED
▶ RESUME unfinished work
check_tracking START prepared=True
check_tracking DONE tracking='IN_TRANSIT'
finish_ticket START tracking='IN_TRANSIT'
finish_ticket DONE
FINAL STATE {'ticket': 'My parcel is late.', 'prepared': True, 'tracking': 'IN_TRANSIT', 'resolution': 'Ask the courier to investigate the delay.'}
```
Preparation ran once; tracking ran twice. This demo caught an exception and resumed in the same Python process using InMemorySaver. It was not a simulated operating-system process restart.

## Three invocation cases
| Call | Meaning |
| --- | --- |
| invoke(new_input, thread_config) | Apply new input and start execution from the graph entry |
| invoke(None, latest_thread_config) | Continue pending work from the latest checkpoint; a completed graph has no pending work |
| invoke(None, historical_snapshot.config) | Replay execution after the selected earlier checkpoint |

None means no new input. It does not mean the result is None. The restored execution can return a full state dictionary.

## Replay selection
```python
before_chat = None
for snapshot in chatbot.get_state_history(chat_config):
    if snapshot.next == ("chat_node",):
        before_chat = snapshot
        break

if before_chat is not None:
    result = chatbot.invoke(None, config=before_chat.config)
```
Historical config includes a checkpoint address. A thread-only config selects the latest state. Replaying after a selected checkpoint can repeat LLM/tool calls; it does not simply display a cached transcript.

## Pending writes
If parallel work partially succeeds, checkpoint pending writes can preserve successful task outputs so they need not repeat on resume. That is distinct from choosing an arbitrary historical checkpoint for replay. A node re-executed after failure begins at its function entry, not the exact failed Python statement.

## In production
External side effects need idempotency. Restoring state does not guarantee an email, refund request, or job post executes exactly once. Define recovery and compensation around business actions.

## Interview questions
::: question What if invoke(None) targets a completed latest checkpoint?
There is no pending node to execute. It is not automatically a new conversation turn.
:::
::: question Why does recovery differ from retrying the whole script?
Recovery uses saved execution progress and pending work. Restarting the entire workflow may repeat successful actions.
:::

## References
- [Checkpointers and replay](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- [Time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
