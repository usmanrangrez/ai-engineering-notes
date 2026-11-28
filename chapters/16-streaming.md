## What it is and why it matters
invoke() returns after execution completes. Streaming exposes intermediate results so a caller can react while the graph is still running. It improves time to visible output; it does not inherently shorten total generation time.

## Learn from the beginning
**Prerequisite:** graph execution and state updates. Your goal is to choose an observable event type and decode its actual Python shape without confusing it with saved state.

### Concept 1 — Streaming yields intermediate observations
**Streaming** lets an application consume events while an execution is running. `invoke` returns after completion; `stream` returns an iterator that yields selected events. Streaming itself does not choose graph routes or guarantee faster model inference. It can improve time to the first visible progress or text.

::: visual streaming-modes | Interactive replay comparing invoke() against messages, updates, values, and custom stream modes

```text
invoke: START ----------------------------- final result
stream: START -- update -- progress -- text chunks -- completion
```

A **chunk** is one delivered piece. A text chunk can be punctuation, part of a word, several words, or empty metadata; it is not necessarily one whole English word or exactly one provider token.

### Concept 2 — Select the output shape deliberately
The following describes the practiced stream-mode API with `version="v1"`. Newer documentation also offers event streaming; this chapter explains the original labs explicitly instead of silently mixing return formats.

| Mode | Payload in this lesson | Question it answers |
| --- | --- | --- |
| updates | node name → state update dictionary | What did that node return? |
| values | current full state dictionary | What is the state after this boundary? |
| messages | pair of message chunk and metadata | What model text is arriving, and from where? |
| custom | application-defined data | What domain progress should we display? |

```python
for update in graph.stream(inputs, stream_mode="updates", version="v1"):
    for node_name, delta in update.items():
        print(node_name, delta, flush=True)
```

`flush=True` requests immediate print-buffer flushing. It avoids confusing buffered terminal output with a graph that did not emit anything. For `messages`, unpack `message_chunk, metadata`; the metadata's `langgraph_node` can help filter which model-producing node to show.

### Concept 3 — Events and durable state are separate channels
```python
from langgraph.config import get_stream_writer

def prepare_reply(state):
    writer = get_stream_writer()
    writer({"stage": "drafting"})
    return {"reply": "Please provide your order ID."}
```

The **stream writer** emits custom progress inside a running graph context. This node emits stage data and returns reply state. Only the returned state update is merged as reply; emitting `{"stage": ...}` does not automatically add a stage field to the checkpoint. Calling a node with get_stream_writer directly outside the execution context is not the same as running it through the graph.

## Build it in small pieces
Start with updates on two deterministic nodes. Change only stream_mode to values and inspect how payloads differ. Then emit one custom event. The [offline streaming lab](../examples/16_streaming.py) combines updates and custom events so you can inspect real envelopes without requiring a model.

With a list of modes under v1, the outer shape is `mode, payload`. If mode is messages, payload itself is `message_chunk, metadata`. Unpack two levels rather than treating every payload as a dictionary. The historical model-token receipt below illustrates messages mode; the offline sample does not pretend a fixed string is live model-token generation.

A completed stream iterator does not return the final invoke dictionary through your loop variable. Accumulate needed values or, with a checkpointer, read get_state after completion. If streaming fails, some text may already have been shown even though the node never returned its final state update. Cancellation, persistence, and UI cleanup need deliberate handling.

## Check your understanding
Predict which modes include ticket, which show only a new reply, and whether a custom drafting event appears in saved state.

::: question Exercise receipt: compare payloads
Run updates and values separately on the same two-node graph. Paste one payload from each and mark the unchanged input key.
:::
::: question Exercise receipt: prove event/state separation
Emit a custom stage. After the stream, inspect the saved keys and show that stage is absent unless explicitly returned as a state field.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/16_streaming.py). Run from the repository root:

```bash
uv run examples/16_streaming.py
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
from langgraph.config import get_stream_writer
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    ticket: str
    category: NotRequired[str]
    reply: NotRequired[str]

def classify(state):
    log("classify START")
    return {"category": "delivery"}

def prepare(state):
    log("prepare START")
    writer = get_stream_writer()
    writer({"stage": "drafting"})
    time.sleep(.05)
    writer({"stage": "completed"})
    return {"reply": "Please provide your order ID."}

builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_node("prepare", prepare)
builder.add_edge(START, "classify")
builder.add_edge("classify", "prepare")
builder.add_edge("prepare", END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "stream-demo"}}

if __name__ == "__main__":
    for mode, payload in graph.stream({"ticket": "My parcel is late."}, config=config, stream_mode=["updates", "custom"], version="v1"):
        log(f"{mode.upper()} {payload}")
    saved = graph.get_state(config)
    assert "stage" not in saved.values and "reply" in saved.values
    log(f"SAVED keys={sorted(saved.values)} next={saved.next}")
```
:::

Author verification output (elapsed times vary):

```text
[  0.26s] classify START
[  0.26s] UPDATES {'classify': {'category': 'delivery'}}
[  0.26s] prepare START
[  0.26s] CUSTOM {'stage': 'drafting'}
[  0.31s] CUSTOM {'stage': 'completed'}
[  0.31s] UPDATES {'prepare': {'reply': 'Please provide your order ID.'}}
[  0.31s] SAVED keys=['category', 'reply', 'ticket'] next=()
```

| Trace observation | What it establishes |
| --- | --- |
| CUSTOM and UPDATES have different envelopes | Progress events and node-returned state updates are separate observations. |
| SAVED keys omit stage | Custom events were not automatically persisted as graph-state fields. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
updates emits node deltas; values emits the state view; messages emits message-chunk/metadata pairs; custom emits application events. In v1 multiple-mode streams add an outer mode/payload pair. Saved state contains returned state fields, not every emitted event.
:::

## Historical learner lab record

## Output shapes used in file 18
These labs explicitly used version="v1". Newer format v2 wraps events with type, ns, and data. Current documentation also offers an event-streaming API; these notes preserve the stream-mode API actually practiced.

| Mode | Each yielded value with one v1 mode |
| --- | --- |
| updates | Node-name dictionary containing its returned changes |
| values | Complete accumulated state, including the initial input event |
| messages | Tuple of (message_chunk, metadata) |
| custom | Payload passed to the stream writer |

## Lab 18A: updates versus values
```bash
uv run 18_support_ticket_streaming.py
```
```text
[  0.51s] UPDATE: {'classify_ticket': {'category': 'delivery'}}
[  1.01s] UPDATE: {'prepare_reply': {'reply': 'Please provide your order ID so support can check tracking.'}}
```
After changing stream_mode to values:
```text
[  0.00s] STATE: {'ticket': 'My parcel is late.'}
[  0.51s] STATE: {'ticket': 'My parcel is late.', 'category': 'delivery'}
[  1.01s] STATE: {'ticket': 'My parcel is late.', 'category': 'delivery', 'reply': 'Please provide your order ID so support can check tracking.'}
```

## Lab 18B: model text
```python
for message_chunk, metadata in graph.stream(
    initial_state, stream_mode="messages", version="v1"
):
    if message_chunk.content:
        log(f"CHUNK node={metadata['langgraph_node']} text={message_chunk.content!r}")
```
```text
[  0.51s] ▶ prepare_reply START
[  0.73s] CHUNK node=prepare_reply text='I'
[  0.73s] CHUNK node=prepare_reply text='’m'
[  0.73s] CHUNK node=prepare_reply text=' sorry'
[  0.78s] ■ prepare_reply DONE
```
Chunks are not guaranteed to be words or exactly one tokenizer token. Empty content can occur. A graph state field called messages is not required for messages mode. LangChain model calls can emit these events even when the node itself calls llm.invoke().

## Lab 18C: custom progress and combined modes
```python
from langgraph.config import get_stream_writer

def prepare_reply(state):
    writer = get_stream_writer()
    writer({"stage": "drafting", "detail": "Preparing a support reply."})
    response = llm.invoke(messages)
    writer({"stage": "completed", "detail": "Support reply generated."})
    return {"reply": response.content}
```
```python
for mode, data in graph.stream(
    initial_state,
    config=chat_config,
    stream_mode=["custom", "messages"],
    version="v1",
):
    if mode == "custom":
        log(f"PROGRESS: {data!r}")
    elif mode == "messages":
        chunk, metadata = data
        if chunk.content:
            log(f"TEXT node={metadata['langgraph_node']} content={chunk.content!r}")
```
Multiple v1 modes yield (mode, data); messages data is another tuple. Two selected modes still observe one graph execution and one model call.

## Lab 18D: persistence after streaming
```text
[  0.51s] PROGRESS: {'stage': 'drafting', 'detail': 'Preparing a support reply.'}
[  0.95s] TEXT node=prepare_reply content='I'
[  1.00s] ■ prepare_reply DONE
[  1.00s] PROGRESS: {'stage': 'completed', 'detail': 'Support reply generated.'}
[  1.01s] SAVED KEYS: ['category', 'reply', 'ticket']
[  1.01s] NEXT NODES: ()
SAVED REPLY: I’m sorry to hear your parcel is delayed. Could you please provide your order ID so we can investigate the delivery status?
```
writer() emits an event; it does not update graph state. The node's return saved the complete reply. The writer and consumer log separately, so a queued event can be printed after the node's DONE log.

## In production
Separate API transport streaming from graph events. If a user stops display, that alone does not guarantee provider generation was cancelled or tokens were saved. Define cancellation and failure handling explicitly.

## Updated refresh receipt (2026-11-28: `31_streaming_modes.py`)
Testing combined `stream_mode=["messages", "custom"]` on a two-node Groq graph (`classify_node` → `reply_node`) proved both live token delivery (`45` chunks in standalone `messages` mode) and node filtering via `metadata.get("langgraph_node")` so internal classifier tokens (`DEL`, `IVERY`) do not leak into the customer's streamed reply:
```text
-> [status] Classifying ticket internally...
[hidden chunk from classify_node]: DEL
[hidden chunk from classify_node]: IVERY
-> [status] Internal label decided: DELIVERY
-> [status] Streaming reply to customer...
(SHOWN from reply_node: 22 | HIDDEN from classify_node: 2)
```

## Interview questions
::: question Must I join chunks to persist the final answer?
Not in this lab. The node's llm.invoke() returns the assembled response, which the node stores in state. Joining chunks may still be needed for other consumer designs.
:::
::: question Does streaming make two sequential nodes parallel?
No. It changes observation and delivery, not the graph's dependencies.
:::

## References
- [Stream modes and v1/v2 formats](https://docs.langchain.com/oss/python/langgraph/streaming)
