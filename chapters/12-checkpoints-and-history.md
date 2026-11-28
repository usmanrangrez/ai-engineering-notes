## What it is and why it matters
The chatbot cannot answer a follow-up about an order ID unless previous messages are restored. A checkpointer saves graph state by thread and by execution boundary.

::: concept The 4 superpowers unlocked by Persistence
1. **Short-term memory:** multi-turn conversations isolated per `thread_id`.
2. **Fault tolerance:** crash at Step 2 → resume from Step 2 via `invoke(None, config)` without redoing Step 1.
3. **Human-in-the-Loop:** durable pausing at `interrupt()` and waking via `Command(resume=...)` (Chapter 24).
4. **Time travel & forking:** inspect every intermediate super-step (`get_state_history`) and branch timelines (`update_state`).
:::

::: warning `get_state` is a read—`thread_id` is NOT authorization
Calling `graph.get_state(config)` reads saved snapshots without calling the LLM. Always verify that the authenticated user owns `thread_id` before loading or invoking a thread in production.
:::

## Learn from the beginning
**Prerequisite:** message reducers from chapter 11. Your goal is to explain the path from an incoming follow-up to a restored conversation without saying “the model remembers.”

### Concept 1 — Persistence saves application state outside one invocation
**Persistence** means retaining data for later use. A **checkpointer** is the component that saves graph execution records. A **checkpoint** is a saved execution boundary containing state and continuation information. A **snapshot** is the object returned when you inspect such saved state.

::: visual persistence-checkpoints | Interactive super-step checkpoints and isolated thread switcher

```text
new input + thread ID
          |
load latest saved state for that thread
          |
merge new input using reducers --> execute nodes --> save new checkpoints
```

An in-memory checkpointer uses the Python process's RAM. Reusing it across calls preserves state during that process; creating a new saver each turn starts new storage. It cannot survive process exit. A thread ID is the lookup identity; it is not the storage itself.

### Concept 2 — Thread ID chooses which history is restored
```python
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()
chatbot = builder.compile(checkpointer=checkpointer)
chat_config = {"configurable": {"thread_id": "learning-chat"}}
```

`configurable` contains execution settings rather than message state. On each turn, send only the new message with the same configuration. If saved state has human + assistant, the new human is merged into it, so the node sees three messages. The returned assistant produces four. A different thread ID selects a different history.

**The model sees remembered facts because the application restores them and sends them in its prompt.** Saving a custom order_id field alone would not inform the model unless the node includes it in messages. A thread ID is also not authentication: an application must check that the caller owns the conversation.

### Concept 3 — State inspection is not model execution
```python
snapshot = chatbot.get_state(chat_config)
print(snapshot.values)
print(snapshot.next)
```

`get_state` reads one saved snapshot; it does not ask the model anything. `values` is its state dictionary. `next` is a tuple of scheduled node names. An empty tuple means no pending graph nodes, not that the conversation has been deleted.

`get_state_history` produces an iterator of snapshots, newest first. An **iterator** yields items when consumed, rather than necessarily allocating a full list immediately. A `for` loop reads one snapshot at a time. `list(history)` materializes them; after consuming an iterator, do not assume it can be iterated again without creating a new one.

## Read the execution boundary
For START → chat_node → END, the historical receipt has a pre-input checkpoint, an input-merged checkpoint scheduling chat_node, and a post-node checkpoint. You can continue from a saved boundary, not from an arbitrary line halfway through `llm.invoke`.

An **execution step** is not a user turn. One turn can traverse several nodes and several steps. Python's own loop counter, checkpoint metadata step, and conversation-message count measure different things. This explains why the three numbers do not advance together.

The [offline persistence lab](../examples/12_persistence.py) invokes a deterministic chat node twice, prints restored counts, and reads both current state and checkpoint history. No model or key is involved.

## Check your understanding
Predict the node's second message count with the same thread ID. Then change the ID and predict the count again before running.

::: question Exercise receipt: prove isolation
Save one message in thread A. Read thread B without invoking it. Paste its empty messages and explain why that read does not create an AI answer.
:::
::: question Exercise receipt: distinguish histories
Print len(snapshot.values["messages"]) for the latest snapshot, then the number of snapshots in get_state_history. Explain why they need not be equal.
:::


## Runnable example and verified trace

Offline lab (no API key or model call required; [setup guide](../start.html)):

[Open the complete Python file](../examples/12_persistence.py). Run from the repository root:

```bash
uv run examples/12_persistence.py
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

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat(state):
    count = len(state["messages"])
    log(f"chat START messages={count}")
    return {"messages": [AIMessage(content=f"I received {count} messages.")]}

builder = StateGraph(State)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)
chatbot = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "persistence-demo"}}

if __name__ == "__main__":
    for text in ["My order ID is ORDER-EXAMPLE.", "What is my order ID?"]:
        result = chatbot.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        log(f"FINAL messages={len(result['messages'])}")
    snapshot = chatbot.get_state(config)
    assert len(snapshot.values["messages"]) == 4
    log(f"CURRENT next={snapshot.next}")
    for saved in chatbot.get_state_history(config):
        log(f"CHECKPOINT step={saved.metadata.get('step')} messages={len(saved.values.get('messages', []))} next={saved.next}")
    other = chatbot.get_state({"configurable": {"thread_id": "fresh-demo"}})
    assert other.values.get("messages", []) == []
    log("FRESH THREAD messages=0")
```
:::

Author verification output (elapsed times vary):

```text
[  0.23s] chat START messages=1
[  0.23s] FINAL messages=2
[  0.23s] chat START messages=3
[  0.23s] FINAL messages=4
[  0.23s] CURRENT next=()
[  0.23s] CHECKPOINT step=4 messages=4 next=()
[  0.23s] CHECKPOINT step=3 messages=3 next=('chat',)
[  0.23s] CHECKPOINT step=2 messages=2 next=('__start__',)
[  0.23s] CHECKPOINT step=1 messages=2 next=()
[  0.23s] CHECKPOINT step=0 messages=1 next=('chat',)
[  0.23s] CHECKPOINT step=-1 messages=0 next=('__start__',)
[  0.23s] FRESH THREAD messages=0
```

| Trace observation | What it establishes |
| --- | --- |
| Second chat START messages=3 | The saver restored two prior messages and merged the new human input. |
| FRESH THREAD messages=0 | A different ID selected a separate saved history. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
The same saved thread gives node input counts one then three, and output counts two then four. Another thread starts separately. get_state reads one snapshot; get_state_history iterates execution snapshots, each of which may contain its own message list.
:::

## Historical learner lab record

```python
checkpointer = InMemorySaver()
chatbot = builder.compile(checkpointer=checkpointer)
chat_config = {"configurable": {"thread_id": "support-demo-1"}}

result = chatbot.invoke(
    {"messages": [HumanMessage(content=user_input)]},
    config=chat_config,
)
```
**Thread ID:** identifies one conversation/execution history. It is not a Python execution thread, a message ID, an order ID, or an authorization credential.

## Lab: saved context and history
```text
You: My order ID is ORDER-EXAMPLE.
chat_node START messages=1
graph DONE messages=2
You: What is my order ID?
chat_node START messages=3
graph DONE messages=4
AI: Your order ID is ORDER-EXAMPLE.
```
The second node input was prior human + prior AI + new human. The final response made four stored messages.

```text
You: /history
SAVED HISTORY thread='support-demo-1' messages=4
1. HumanMessage: My order ID is ORDER-EXAMPLE.
2. AIMessage: Could you let me know what issue you’re experiencing with order ORDER-EXAMPLE?
3. HumanMessage: What is my order ID?
4. AIMessage: Your order ID is ORDER-EXAMPLE.
```

## One snapshot versus an iterator
```python
snapshot = chatbot.get_state(chat_config)
messages = snapshot.values.get("messages", [])

for snapshot in chatbot.get_state_history(chat_config):
    print(snapshot.metadata.get("step"), snapshot.next)
```
get_state returns one StateSnapshot. get_state_history returns an iterator of snapshots, newest first; list(...) materializes it. Both read state without calling the model.

| Snapshot field | Meaning |
| --- | --- |
| values | Saved state dictionary |
| next | Tuple of scheduled node names; () means no pending nodes |
| config | Thread and checkpoint address |
| metadata | Execution metadata, including graph step |

## Super-step receipt
```text
CHECKPOINT step=1 messages=2 next=()
CHECKPOINT step=0 messages=1 next=('chat_node',)
CHECKPOINT step=-1 messages=0 next=('__start__',)
```
These are execution-boundary snapshots, not simply one checkpoint per visible diagram label. The initial/input boundary and the completed-node boundary are distinct.

## Selecting a checkpoint without hiding Python syntax
```python
before_chat = None
for snapshot in chatbot.get_state_history(chat_config):
    if snapshot.next == ("chat_node",):
        before_chat = snapshot
        break
```
The tuple's trailing comma makes it a one-item tuple. snapshot.next is an attribute, not the built-in next(). A compact equivalent is next((s for s in history if condition), None); prefer the loop when debugging.

## In production
InMemorySaver survives repeated calls in the same process but not process exit. Checkpointing is thread-scoped memory, not automatically cross-thread long-term memory. Keep application ownership checks outside the assumption that knowing an ID grants access.

## Updated redo receipt (2026-11-27: `28_persistence_basics.py`)
Running a deterministic two-node workflow (`classify` → `draft_reply`) across two isolated threads (`ticket-A` and `ticket-B`) confirmed newest-first checkpoint history and thread isolation:
```text
LATEST ticket-A values: {'ticket': 'Order ORD-42 is late', 'category': 'delivery', 'reply': 'Handling delivery request for: Order ORD-42 is late'}
LATEST ticket-A next: ()

HISTORY for ticket-A (newest first):
  next=() | values={'ticket': 'Order ORD-42 is late', 'category': 'delivery', 'reply': 'Handling delivery request for: Order ORD-42 is late'} | cp_id=<CHECKPOINT_ID>
  next=('draft_reply',) | values={'ticket': 'Order ORD-42 is late', 'category': 'delivery'} | cp_id=<CHECKPOINT_ID>
  next=('classify',) | values={'ticket': 'Order ORD-42 is late'} | cp_id=<CHECKPOINT_ID>
  next=('__start__',) | values={} | cp_id=<CHECKPOINT_ID>
```

## Interview questions
::: question Is get_state_history the chat message history?
No. It is graph checkpoint history. Each snapshot may contain a growing conversation in its values.
:::
::: question Why do two user turns not mean step=2?
A turn can involve several super-steps. A Python turn counter and graph step metadata measure different things.
:::

## References
- [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)
