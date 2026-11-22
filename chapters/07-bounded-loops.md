## What it is and why it matters
A reply can exceed the required word limit. One repair call might still be too long, so send it back to a deterministic checker. Unbounded repetition spends tokens without guaranteeing progress.

## Learn from the beginning
**Prerequisite:** conditional edges. Your goal is to distinguish an acceptable result from a workflow that merely stopped consuming resources.

### Concept 1 — A loop is an edge back to earlier work
A **loop** repeats a portion of the graph. A **bounded loop** has an explicit condition limiting repetitions. For a short support reply, check its word count, repair it if necessary, then check the new reply rather than assuming the repair worked.

```text
                     good --------------------> END
START --> check ---- too long --> repair --+
             ^                            |
             +----------------------------+
             | budget exhausted -------------> END (unresolved)
```

The backward edge creates repetition; the router decides whether to traverse it. It is a workflow cycle, not recursive Python function calls. The repair node must increment a counter and return its new reply so the next check measures new data.

### Concept 2 — Define the counter precisely
Let `repair_attempts=0` mean the initial draft has not been repaired. With `max_repairs=2`, at most two repair operations are allowed; there can be three checks: initial, after repair one, after repair two.

```python
if state["reply_words"] <= WORD_LIMIT:
    return "finish"
if state["repair_attempts"] >= MAX_REPAIRS:
    return "limit_exceeded"
return "repair"
```

Order matters. If the last permitted repair succeeds, the success check should recognize it before the budget exit. **A budget exit is not approval.** Record or report an unresolved status rather than silently presenting an invalid reply as compliant. Mapping two exit labels to END is allowed, but logging the reason is still necessary.

### Concept 3 — The runtime limit is an independent backstop
`graph.invoke(input_state, config={"recursion_limit": 20})` puts a bound on graph super-steps, not words, model tokens, seconds, or exactly twenty repair calls. Other nodes also consume graph rounds. The runtime raises `GraphRecursionError` if execution cannot stop within the configured bound.

The business counter gives a controlled result with a known reason. The runtime limit catches a broken cycle even if your business guard is wrong. Without a checkpointer, a failing invoke does not return a normal final-state dictionary. With a checkpointer, previously saved state can still be inspected and recovered; the error does not mean every saved checkpoint was erased.

## Build it in small pieces
The [offline bounded-loop lab](../examples/07_bounded.py) shortens a reply by one word per repair. This deliberately simple repair makes repeated checks and the attempt count observable without LLM variation. Read the quality measure before deciding whether such a repair is appropriate: deleting words mechanically is not a safe support-writing strategy.

When replacing repair with a model, include the current reply and actual violations in the prompt. A **prompt hash** is a short digest of prompt bytes used to compare prompts without printing their entire contents. A changed hash proves bytes changed, not that feedback was helpful. Hashing private data is not a complete anonymization scheme.

## Check your understanding
Predict the maximum number of repair START lines with a budget of two. Run the lab with an intentionally impossible word limit and observe the unresolved exit.

::: question Exercise receipt: prove the guard
Set max_repairs to zero. Paste the budget-exhausted line and show that no repair START line appears.
:::
::: question Exercise receipt: distinguish limits
Temporarily set recursion_limit to one, catch GraphRecursionError, and paste its type. Explain why increasing it does not fix a missing business stop.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/07_bounded.py). Run from the repository root:

```bash
uv run examples/07_bounded.py
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

from typing import Literal, NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    reply: str
    attempts: int
    max_repairs: int
    word_limit: int
    words: NotRequired[int]

def check(state):
    words = len(state["reply"].split())
    log(f"check words={words}/{state['word_limit']} attempts={state['attempts']}/{state['max_repairs']}")
    return {"words": words}

def route(state) -> Literal["finish", "repair", "limit_exceeded"]:
    if state["words"] <= state["word_limit"]:
        label = "finish"
    elif state["attempts"] >= state["max_repairs"]:
        label = "limit_exceeded"
    else:
        label = "repair"
    log(f"ROUTE {label}")
    return label

def repair(state):
    attempt = state["attempts"] + 1
    log(f"repair START attempt={attempt}")
    # Artificial mechanical repair, not safe production writing.
    reply = " ".join(state["reply"].split()[:-1])
    log(f"repair DONE reply={reply!r}")
    return {"reply": reply, "attempts": attempt}

builder = StateGraph(State)
builder.add_node("check", check)
builder.add_node("repair", repair)
builder.add_edge(START, "check")
builder.add_conditional_edges("check", route, {"finish": END, "repair": "repair", "limit_exceeded": END})
builder.add_edge("repair", "check")
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"reply": "Please provide your order ID now", "attempts": 0, "max_repairs": 2, "word_limit": 5}, config={"recursion_limit": 20})
    assert result["attempts"] == 1 and result["words"] == 5
    log(f"FINAL acceptable={result['words'] <= result['word_limit']}")
```
:::

Author verification output (elapsed times vary):

```text
[  0.23s] check words=6/5 attempts=0/2
[  0.23s] ROUTE repair
[  0.23s] repair START attempt=1
[  0.23s] repair DONE reply='Please provide your order ID'
[  0.23s] check words=5/5 attempts=1/2
[  0.23s] ROUTE finish
[  0.23s] FINAL acceptable=True
```

| Trace observation | What it establishes |
| --- | --- |
| check appears twice | The repaired reply was actually checked again. |
| attempt=1 and ROUTE finish | One repair met the target; the counter did not count the initial draft as a repair. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
With max_repairs=2, there are at most two repair executions, not two total node calls. A zero budget skips repair. Success should be tested before the exhausted-budget branch so a successful final attempt is accepted. Runtime limits count graph rounds.
:::

## Historical learner lab record

```text
draft_reply -> check_reply --valid--> END
                  | too long, budget available
                  v
              repair_reply
                  |
                  +----------> check_reply
```
**Attempt guard:** a state-based business stop. **recursion_limit:** a runtime super-step backstop, not Python call-stack recursion depth and not a count of model retries.

## Lab: file 10
```bash
uv run 10_support_ticket_bounded.py
```
Successful repair receipt:
```text
[  1.11s] check_reply DONE words=35/25 repairs=0/2 too_long=True
[  1.11s] route_reply words=35 repairs=0 -> repair
[  1.11s] repair_reply START attempt=1/2 prompt_hash=df4d5ebe
[  2.17s] repair_reply DONE words=24/25
[  2.17s] check_reply DONE words=24/25 repairs=1/2 too_long=False
[  2.17s] route_reply words=24 repairs=1 -> finish
```
Budget-exit receipt:
```text
check_reply DONE words=46/1 repairs=0/0 too_long=True
route_reply words=46 repairs=0 -> limit_exceeded
FINAL WORD COUNT: 46/1
```
Stopping is not approval. The reply still violated the target after the budget exit.

## Runtime-backstop lab
```python
result = graph.invoke(initial_state, config={"recursion_limit": 1})
```
```text
understand_ticket DONE category='delivery' sentiment='negative'
route_after_understanding -> diagnose_issue
✖ graph STOP: runtime step limit reached
GraphRecursionError: Recursion limit of 1 reached without hitting a stop condition.
```
Only the first processing super-step ran. With no checkpointer, the failed invoke does not return a final result. Earlier teaching shorthand “recursion_limit discards state” was too broad: a checkpointer can preserve committed state for inspection/recovery.

## Prompt invariant
A repair must receive the current reply and actionable violations. Log a hash of the complete repair prompt to check whether relevant input actually changed. A prompt hash is an inspection aid, not proof of improved output.

## In production
Use an attempt cap and runtime backstop as separate safeguards for loops. Return an explicit exit reason. Retry transient provider errors separately from semantic revision; one configured layer should own backoff. SDK max_retries=1 can still allow a retry; it does not mean retries are disabled.

## Interview questions
::: question Can a sequential graph hit recursion_limit?
Yes. It limits graph super-steps, so an excessively small value can stop an acyclic graph too.
:::
::: question What should a budget exit communicate?
The process stopped without necessarily meeting its target. Preserve violations and the exit reason.
:::

## References
- [Graph recursion limit](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT)
- [Checkpointers and recovery](https://docs.langchain.com/oss/python/langgraph/checkpointers)
