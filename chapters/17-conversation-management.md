## What it is and why it matters
One hardcoded thread ID mixes separate conversations. We need a stable ID for each conversation, a readable title, and an active selection.

::: mental-model Two-layer backend: Conversation Directory + Checkpointer
- **Layer 1 (Conversation Directory — app DB/JSON):** stores `{thread_id, title, owner_id, updated_at}` for the sidebar list (newest first).
- **Layer 2 (LangGraph Checkpointer):** stores the actual `messages` and graph checkpoints keyed by `thread_id`.
Clicking a chat in the sidebar looks up its `thread_id` in Layer 1, then loads its messages from Layer 2 via `graph.get_state(config)`.
:::

::: warning Never use a chat title as the `thread_id`
Titles can be renamed or duplicated across users. Always generate an immutable `str(uuid4())` as the primary key and keep the title as editable metadata.
:::

## Learn from the beginning
**Prerequisite:** saved state selected by thread ID. Your goal is to implement “new chat” and “switch chat” without deleting existing conversations or confusing labels with storage keys.

### Concept 1 — A directory locates conversations
A **conversation directory** is an application-managed catalog: IDs, titles, creation information, and ownership. A checkpointer holds graph state. A directory entry points to that state using a thread ID; the title is human-readable metadata.

```text
directory                             checkpointer
ID A -> "Delayed headphones" ---------> thread A: four messages
ID B -> "Account access" --------------> thread B: two messages
active selection: A
```

Renaming “Delayed headphones” should not change the ID. Two conversations can have the same title without being the same conversation. A title is not a good primary key. A **primary key** is the identifier used to uniquely locate a record.

### Concept 2 — New chat selects a new ID
```python
from uuid import uuid4
thread_id = str(uuid4())
```

A **UUID** is a widely used identifier format. UUID version four uses randomness to make accidental collisions extremely unlikely; it is not a password or proof of ownership. `str` converts the UUID object into a string suitable for the configuration.

`reset_chat` in the lesson is an ordinary application function, not a LangGraph API. Its job is to create/select a new ID, register a title, and clear the currently displayed messages. It does not need to delete the previous checkpoint history. A fresh directory entry may have no checkpoint yet because no message has been sent.

### Concept 3 — Switching reads another saved state
```python
def load_conversation(chatbot, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = chatbot.get_state(config)
    return snapshot.values.get("messages", [])
```

`.get("messages", [])` handles a new thread whose message key is absent. Loading history does not invoke chat_node. To continue that chat, send only the new human message with the selected thread's configuration. Sending a copied transcript and using a saver simultaneously can duplicate or replace data unexpectedly if message identities are mishandled.

**Active selection is an application variable; saved conversations are independent records.** Changing active_thread_id does not move messages between records. Keep message loading, selection, and new-turn invocation as separate responsibilities so each can be tested.

## Build it in small pieces
Write `add_thread(directory, id, title)` so adding an existing ID does not create a duplicate catalog entry. Then create two IDs and invoke one deterministic message in each. Read both. Select the first and invoke a second message. Finally create a third ID and verify its history is empty while the first still has four messages.

The [offline directory lab](../examples/17_threads.py) carries out that sequence with InMemorySaver. It logs only symbolic thread labels in its receipt so public output does not contain randomly generated identifiers. The original learner-run directory behavior appears below.

In production, list only conversations the authenticated user is permitted to access. An authenticated user is a verified caller; authorization is the decision that this caller may read a particular conversation. Knowing a UUID must not bypass that check.

## Check your understanding
Predict whether “new chat” should call a delete API. Then explain how both the previous four-message chat and new empty chat can exist simultaneously.

::: question Exercise receipt: prove switching
Send a second turn in A and read B. Paste counts A=4 and B=2. Show which configuration selected each.
:::
::: question Exercise receipt: prove deduplication
Call add_thread twice with the same ID. Paste the unchanged directory length and explain why different titles alone should not create a second record with that ID.
:::


## Runnable example and verified trace

Offline lab (no API key or model call required; [setup guide](../start.html)):

[Open the complete Python file](../examples/17_threads.py). Run from the repository root:

```bash
uv run examples/17_threads.py
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

from uuid import uuid4
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat(state):
    log(f"chat START messages={len(state['messages'])}")
    return {"messages": [AIMessage(content="Message received.")]}

def add_thread(directory, thread_id, title):
    if thread_id not in directory:
        directory[thread_id] = {"title": title}

def load_conversation(chatbot, thread_id):
    return chatbot.get_state({"configurable": {"thread_id": thread_id}}).values.get("messages", [])

def send(chatbot, thread_id, text):
    return chatbot.invoke({"messages": [HumanMessage(content=text)]}, config={"configurable": {"thread_id": thread_id}})

builder = StateGraph(State)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)
chatbot = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    directory = {}
    first, second, fresh = str(uuid4()), str(uuid4()), str(uuid4())
    add_thread(directory, first, "Delayed headphones")
    add_thread(directory, second, "Account access")
    add_thread(directory, first, "Duplicate ID")
    assert len(directory) == 2
    send(chatbot, first, "My headphones are late.")
    send(chatbot, second, "I cannot sign in.")
    active = first
    send(chatbot, active, "My order ID is ORDER-EXAMPLE.")
    a, b = len(load_conversation(chatbot, first)), len(load_conversation(chatbot, second))
    log(f"COUNTS first={a} second={b}")
    assert (a, b) == (4, 2)
    add_thread(directory, fresh, "New chat")
    active = fresh
    assert load_conversation(chatbot, active) == []
    assert len(load_conversation(chatbot, first)) == 4
    log(f"FRESH messages=0 directory={len(directory)} first_preserved=True")
```
:::

Author verification output (elapsed times vary):

```text
[  0.22s] chat START messages=1
[  0.22s] chat START messages=1
[  0.23s] chat START messages=3
[  0.23s] COUNTS first=4 second=2
[  0.23s] FRESH messages=0 directory=3 first_preserved=True
```

| Trace observation | What it establishes |
| --- | --- |
| COUNTS first=4 second=2 | Continuing the selected conversation did not change the other one. |
| FRESH messages=0 first_preserved=True | Creating a new chat changed selection without deleting prior state. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
New chat selects a fresh ID; it does not need to delete old checkpoints. Titles are labels and may repeat. A directory deduplicates by ID, while the saver restores messages by that ID. Selection must be paired with ownership checks in production.
:::

## Historical learner lab record

```text
Directory: ID -> title
Checkpoint storage: ID -> saved graph history
Active ID: the selected conversation for the next request
```
**UUID:** a standard identifier format. uuid4() generates a random UUID; practical collision probability is negligible, not mathematically zero.

## Application helpers
```python
conversations: dict[str, str] = {}

def generate_thread_id() -> str:
    return str(uuid.uuid4())

def add_thread(thread_id: str, title: str) -> None:
    if thread_id not in conversations:
        conversations[thread_id] = title

def new_chat(title: str) -> str:
    thread_id = generate_thread_id()
    add_thread(thread_id, title)
    return thread_id
```
A dictionary membership check tests keys. The ID identifies one conversation, not a person. Two conversations may legitimately have the same title.

## Lab: file 19
```bash
uv run 19_support_ticket_threads.py
```
Initial directory stage:
```text
ADDED title='Delayed headphones' id=<THREAD_A>
ADDED title='Account access' id=<THREAD_B>
SKIPPED existing id=<THREAD_A>
CONVERSATION COUNT: 2
ACTIVE TITLE: 'Account access'
FIRST STILL EXISTS: True
```
With a graph and InMemorySaver:
```text
chat_node START messages=1
chat_node START messages=1
FIRST SAVED USER: 'My headphones are late.'
SECOND SAVED USER: 'I cannot sign in.'
SWITCHED TO: 'Delayed headphones'
chat_node START messages=3
FIRST MESSAGE COUNT: 4
SECOND MESSAGE COUNT: 2
```
The deterministic node constructed AIMessage("Received: ..."); no model was called. It isolated the storage mechanism from model variability.

## Load history without executing
```python
def load_conversation(thread_id: str) -> list[BaseMessage]:
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = chatbot.get_state(config)
    return snapshot.values.get("messages", [])
```
Then creating and selecting another ID produced:
```text
NEW ACTIVE TITLE: 'Refund question'
NEW HISTORY: []
FIRST STILL HAS: 4 messages
```
New Chat selects a fresh ID. It does not delete old history. Selecting an existing ID is not invoke(None): a new user turn supplies new input with that ID.

## In production
Associate conversations with owners/organizations and check access before reading or invoking. UUIDs are addresses, not permissions. Our directory and in-memory histories still vanished when that Python process exited; the next chapter fixes both lifetimes.

## Interview questions
::: question Does new_chat() itself create checkpoint messages?
No. It registers an ID and title. Checkpoints appear when the graph saves execution state.
:::
::: question Is the title the lookup key?
No. The stable thread ID is the key. Titles are labels and can change.
:::

## References
- [Python UUID](https://docs.python.org/3.14/library/uuid.html)
- [LangGraph threads](https://docs.langchain.com/oss/python/langgraph/checkpointers#threads)
