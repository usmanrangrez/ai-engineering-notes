## What it is and why it matters
One hardcoded thread ID mixes separate conversations. We need a stable ID for each conversation, a readable title, and an active selection.

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
