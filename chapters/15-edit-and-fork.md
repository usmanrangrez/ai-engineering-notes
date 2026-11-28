## What it is and why it matters
Editing an order ID after the model answered should regenerate the answer using the correction. Merely changing the last completed state does not necessarily schedule the chat node again.

::: mental-model Time-travel forking works like `git branch`
Calling `graph.update_state(past_snap.config, new_values)` **never deletes** the old checkpoints—it creates a new child checkpoint branching off `past_snap`'s `checkpoint_id` (which is why our live run grew from `4` checkpoints to `7`). Invoking `graph.invoke(None, config=fork_config)` then executes forward along the new branch.
:::

::: warning Replace vs. Append in `MessagesState`
With `add_messages`, passing a `HumanMessage` with the **same `id`** replaces that message; omitting the `id` (or creating a fresh ID) **appends** a second message instead.
:::

## Learn from the beginning
**Prerequisite:** message IDs, checkpoints, and replay. Your goal is to edit one message and regenerate only the response that depends on the corrected conversation.

### Concept 1 — Replacing a message and appending a correction differ
If a user types “Actually my order ID is ORDER-NEW,” that is a new message in the same conversation. If they edit their earlier message, they expect the earlier contribution to change. `add_messages` distinguishes messages by ID; returning the same ID with changed content replaces that message in the reducer's result.

```python
replacement = HumanMessage(id=original.id, content="My order ID is ORDER-NEW.")
```

Changing the content while generating a new ID generally appends a new message. The role matters too: replace the intended human message, not whichever item happens to be last. A thread ID selects a history; a message ID selects an item within message state.

### Concept 2 — Choose a checkpoint before the dependent answer
::: visual persistence-time-travel | Time-travel fork diagram showing 4 original checkpoints growing to 7

```text
original: human OLD --> checkpoint C --> assistant OLD
                              |
update human with same ID --> new checkpoint C2 --> assistant NEW
```

A **fork** creates a new continuation from a selected saved boundary. Merely replacing a human message in a finished state can leave a stale assistant answer alongside it. For this one-node chatbot, select the snapshot where the target human message is already present and chat_node is next. Then update that snapshot's state and continue from the returned configuration.

```python
fork_config = chatbot.update_state(
    before_chat.config,
    {"messages": [replacement]},
    as_node="__start__",
)
result = chatbot.invoke(None, config=fork_config)
```

`update_state` creates a state update/checkpoint; it does not call the model. `as_node` tells the graph which node the update should be attributed to so downstream scheduling can be determined. In this START → chat_node graph, attributing the input update to START leaves chat_node next. This is graph-specific; using the same value blindly in a different graph can schedule the wrong continuation.

### Concept 3 — The checkpoint address matters after a fork
Use `fork_config`, not a loosely remembered configuration. It identifies the state you just created. Old checkpoints remain historical records; this is not a destructive rewrite of every past version. In a real UI, decide which fork is the active conversation and make that choice explicit.

Find the checkpoint with an ordinary loop before using compact syntax. `snapshot.next == ("chat_node",)` compares an attribute to a one-item tuple. The comma creates the tuple. Python's built-in `next(iterator, default)` retrieves an item from an iterator; it is a different use of the word next.

`f"{text!r}"` formats `repr(text)`, exposing quotes and escape sequences. It helps distinguish an empty string, spaces, or newlines when logging edits. It is a display conversion, not a replacement or persistence operation.

## Build it in small pieces
The [offline edit/fork lab](../examples/15_edit.py) makes one deterministic reply, selects the pre-chat checkpoint, replaces the human message with the same ID, and invokes the fork. Its result checks both message count and the changed reply. The deterministic reply proves data flow without claiming a model will always follow an instruction perfectly.

Editing an old message in a multi-turn conversation requires selecting that message's relevant checkpoint and deciding what to do with all later turns. The latest pre-chat checkpoint may concern a later message. This lab deliberately handles one turn so that ambiguity is visible rather than hidden.

## Check your understanding
Predict: will the new conversation have two messages or three? Which assistant answer should remain in the fork's final state?

::: question Exercise receipt: break identity
Give replacement a fresh ID. Paste the increased count and explain why this was an append rather than a replacement.
:::
::: question Exercise receipt: prove regeneration
Paste original human ID and replacement ID as placeholders, plus the two different assistant contents. State which node ran after update_state.
:::


## Runnable example and verified trace

Offline lab (no API key or model call required; [setup guide](../start.html)):

[Open the complete Python file](../examples/15_edit.py). Run from the repository root:

```bash
uv run examples/15_edit.py
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
    log(f"chat START messages={len(state['messages'])}")
    human = next(m for m in reversed(state["messages"]) if isinstance(m, HumanMessage))
    return {"messages": [AIMessage(content=f"Received: {human.content}")]}

builder = StateGraph(State)
builder.add_node("chat_node", chat)
builder.add_edge(START, "chat_node")
builder.add_edge("chat_node", END)
chatbot = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "edit-demo"}}

if __name__ == "__main__":
    original = chatbot.invoke({"messages": [HumanMessage(content="My order ID is ORDER-OLD.")]}, config=config)
    log(f"ORIGINAL {original['messages'][-1].content}")
    before_chat = None
    for snapshot in chatbot.get_state_history(config):
        if snapshot.next == ("chat_node",):
            before_chat = snapshot
            break
    if before_chat is None:
        raise RuntimeError("No pre-chat checkpoint found")
    human = before_chat.values["messages"][0]
    replacement = HumanMessage(id=human.id, content="My order ID is ORDER-NEW.")
    fork_config = chatbot.update_state(before_chat.config, {"messages": [replacement]}, as_node="__start__")
    fork = chatbot.get_state(fork_config)
    log(f"FORK messages={len(fork.values['messages'])} next={fork.next}")
    result = chatbot.invoke(None, config=fork_config)
    assert len(result["messages"]) == 2
    assert "ORDER-NEW" in result["messages"][-1].content
    log(f"EDITED {result['messages'][-1].content}")
```
:::

Author verification output (elapsed times vary):

```text
[  0.23s] chat START messages=1
[  0.23s] ORIGINAL Received: My order ID is ORDER-OLD.
[  0.23s] FORK messages=1 next=('chat_node',)
[  0.23s] chat START messages=1
[  0.23s] EDITED Received: My order ID is ORDER-NEW.
```

| Trace observation | What it establishes |
| --- | --- |
| FORK messages=1 next=chat_node | The selected boundary contains only the corrected input and schedules regeneration. |
| EDITED mentions ORDER-NEW | The downstream reply used the corrected message, without preserving a stale assistant answer. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
The fork should contain a corrected human message and one regenerated answer. Reusing the message ID replaces it; a fresh ID appends it. Updating a finished conversation without removing dependent stale turns is a different operation and can leave inconsistent history.
:::

## Historical learner lab record

## Mechanism
```text
Earlier checkpoint: Human(original ID), next=chat_node
        |
        +-- update_state with Human(same message ID, new content)
                  |
                  +-- new checkpoint, next=chat_node
                            |
                            +-- invoke(None, edited checkpoint config)
```
**Fork:** a new continuation from existing saved history. The earlier checkpoints remain available.

## Important code shape
```python
old_message = before_chat.values["messages"][-1]
edited_message = HumanMessage(
    id=old_message.id,
    content="My order ID is ORDER-CORRECTED.",
)
fork_config = chatbot.update_state(
    before_chat.config,
    {"messages": [edited_message]},
)
result = chatbot.invoke(None, config=fork_config)
```
Same message ID makes add_messages replace the item. A new message ID would normally append another message instead. update_state applies normal field reducer semantics; it is not an unrestricted mutation of old checkpoint rows.

## Lab: file 17
```bash
uv run 17_support_chatbot_edit.py
```
```text
You: /thread edit-demo-1
You: My order ID is ORDER-ORIGINAL.
You: /edit My order ID is ORDER-CORRECTED.
EDIT BEFORE id=<MESSAGE_ID> content='My order ID is ORDER-ORIGINAL.'
EDIT AFTER  id=<MESSAGE_ID> content='My order ID is ORDER-CORRECTED.'
FORK messages=1 next=('chat_node',)
▶ CONTINUE edited checkpoint
chat_node START messages=1
EDIT DONE messages=2
AI: Could you let me know what issue you’re experiencing with order ORDER-CORRECTED?
```
The message ID is the same on both lines. The fork had one message before generation and two afterwards. Exact personal and business identifiers are replaced with placeholders.

## Why select the pre-chat checkpoint?
The latest completed checkpoint normally has next=(). Updating it can be attributed to a completed node and leave no next execution. This lab chose the checkpoint with next=('chat_node',) so the intended regeneration was explicit.

## What !r means
In `f"content={message.content!r}"`, !r formats the value using repr(). It makes quotes and escape characters visible for inspection. It does not alter the stored content.

## In production
Define whether editing an earlier message discards or branches later turns. Our CLI edited the most recent user turn. Editing arbitrary old messages requires an explicit policy for subsequent state and external actions.

## Updated redo receipt (2026-11-28: `29_persistence_time_travel.py`)
Forking from the historical checkpoint with `next=('classify',)` via `graph.update_state(past_snap.config, {"ticket": "Please cancel ORD-99"})` preserved all 4 original checkpoints and appended 3 new forked checkpoints (total `7`):
```text
=== ORIGINAL RUN ===
-> RUNNING classify on: Order ORD-42 is late
-> RUNNING draft_reply for: delivery
ORIGINAL RESULT: {'ticket': 'Order ORD-42 is late', 'category': 'delivery', 'reply': 'Handling delivery request for: Order ORD-42 is late'}

=== FORKED RUN ===
-> RUNNING classify on: Please cancel ORD-99
-> RUNNING draft_reply for: cancellation
FORKED RESULT: {'ticket': 'Please cancel ORD-99', 'category': 'cancellation', 'reply': 'Handling cancellation request for: Please cancel ORD-99'}
HISTORY CHECKPOINTS -> before fork: 4 | after fork: 7
```

## Interview questions
::: question Does changing content alone replace a message?
Replacement depends on matching message IDs with add_messages. Without that identity, the update may be a new message.
:::
::: question Does replay undo an already-sent email?
No. External effects require business-level handling; checkpoint branching does not reverse them.
:::

## References
- [Time travel and state updates](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
- [add_messages](https://reference.langchain.com/python/langgraph/graph/message/add_messages)

- [Time travel and forks](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
