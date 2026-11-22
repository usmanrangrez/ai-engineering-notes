## What it is and why it matters
invoke() returns after execution completes. Streaming exposes intermediate results so a caller can react while the graph is still running. It improves time to visible output; it does not inherently shorten total generation time.

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

## Interview questions
::: question Must I join chunks to persist the final answer?
Not in this lab. The node's llm.invoke() returns the assembled response, which the node stores in state. Joining chunks may still be needed for other consumer designs.
:::
::: question Does streaming make two sequential nodes parallel?
No. It changes observation and delivery, not the graph's dependencies.
:::

## References
- [Stream modes and v1/v2 formats](https://docs.langchain.com/oss/python/langgraph/streaming)
