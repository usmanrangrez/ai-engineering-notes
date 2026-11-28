## What it is and why it matters
Saving checkpoint state is insufficient if the application forgets which conversation IDs exist. Conversely, restoring a directory of titles does not restore RAM-only messages. Persist both responsibilities.

::: concept Prove BOTH layers survive a fresh process
A restart test is only valid when you verify two separate facts in a **new Python process**: (1) the sidebar catalog still lists your conversation IDs and titles, and (2) `graph.get_state(config)` restores the actual `HumanMessage` / `AIMessage` history from SQLite/Postgres.
:::

::: warning Plain JSON files are not concurrency-safe databases
A JSON directory file works fine for single-user local labs, but concurrent HTTP requests doing read-modify-write can overwrite each other. In production FastAPI apps, store the conversation catalog in PostgreSQL alongside (but logically separate from) LangGraph's checkpoint tables.
:::

## Learn from the beginning
**Prerequisite:** conversation directories and SQLite checkpoints. Your goal is to identify which of two kinds of data survived a restart and prove both independently.

### Concept 1 — Metadata and message state can have separate storage
A **metadata record** describes a conversation: title, ID, owner, timestamps. **Graph state** contains its messages and workflow fields. Saving metadata does not automatically save messages, and saving messages does not automatically create your application's preferred titles.

```text
thread_directory.json --> IDs and titles
thread_messages.sqlite --> graph checkpoints and message state
             same thread ID joins the two responsibilities
```

In our first directory lab, a JSON file survived restart but InMemorySaver did not. The list could still display “Delayed headphones” while loading no old messages. That behavior was a missing durable-state backend, not proof that the directory failed to write.

### Concept 2 — JSON is a representation, not a database transaction system
```python
import json
from pathlib import Path

path = Path("data/thread_directory.json")
directory = json.loads(path.read_text()) if path.exists() else {}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(directory, indent=2))
```

This is a small single-process serialization excerpt, not the complete directory manager. `json.dumps` produces JSON text; `json.loads` parses it. `read_text` and `write_text` handle the file. A Python dictionary in memory is different from the saved JSON text. A process can change the dictionary without having saved the change yet.

A **transaction** groups database work under defined commit/rollback guarantees. A plain read-modify-write JSON sequence does not prevent another process from reading old contents and overwriting your update. Atomic replacement can reduce partial-file writes; it does not alone solve concurrent lost updates.

### Concept 3 — Prove metadata and state with separate receipts
| Check | What it proves | What it does not prove |
| --- | --- | --- |
| Restart and list three titles | Directory persisted | Old messages persisted |
| Restart and load four messages for A | A's checkpoint state persisted | Every catalog entry is valid |
| New chat has no messages | Fresh ID selects empty state | Old state was deleted |

The durable version keeps SQLite open while reading/invoking the graph and uses the same IDs from the saved directory. It does not need to reconstruct messages by parsing terminal logs. The checkpointer is the application's state source for that graph history.

## Build it in small pieces
First test metadata-only restart without any model. Then use the SQLite lab from chapter 13 to write/read message state in separate processes. Finally compose those responsibilities: retrieve an ID from the directory and use it to load the matching saved graph state. File 20 in the historical receipt did that final proof with four restored messages.

This lesson does not require memorizing SQL table definitions. It requires knowing which component owns which data and being able to diagnose a blank conversation. In a larger application, a database-backed conversation catalog can store ownership and titles separately from checkpointer-internal tables, even if both use the same database engine. Do not build app features by casually modifying checkpoint internals.

## Check your understanding
Predict whether a saved title is sufficient for an LLM to recall an order ID. It is not: the prompt must contain the restored message/state data relevant to the answer.

::: question Exercise receipt: isolate a failure
Keep the JSON catalog but temporarily use a fresh in-memory saver. Show titles exist and messages do not. Explain the mismatch before changing storage back.
:::
::: question Exercise receipt: restart rather than rerun in memory
Exit the writer process, start a separate reader, and paste the restored four-message transcript with order IDs sanitized.
:::


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Titles surviving restart prove the metadata file persisted. Messages surviving a fresh process prove checkpoint durability. You need both for a useful restored chat list. A JSON file read-modify-write is not a concurrency-safe transactional catalog.
:::

## Historical learner lab record

## Lab 19: JSON directory
```python
DIRECTORY_PATH = Path(__file__).resolve().parent / "data" / "thread_directory.json"

def load_directory() -> dict[str, str]:
    if not DIRECTORY_PATH.exists():
        return {}
    return json.loads(DIRECTORY_PATH.read_text(encoding="utf-8"))
```
add_thread writes json.dumps(conversations, indent=2) after adding a new ID. load_directory runs on startup.

```bash
uv run 19_support_ticket_threads.py
uv run 19_support_ticket_threads.py --list
```
```text
DIRECTORY FILE: <PROJECT_ROOT>/support_ticket/data/thread_directory.json
CONVERSATION title='Delayed headphones' id=<THREAD_A>
CONVERSATION title='Account access' id=<THREAD_B>
CONVERSATION title='Refund question' id=<THREAD_C>
DIRECTORY COUNT: 3
```
The list-only process did not run chat_node. Normal demo runs intentionally create three new IDs each time; list mode does not.

## Lab 20: durable messages
```text
data/
  thread_directory.json   -> ID/title directory
  thread_messages.sqlite  -> checkpoint state
```
```python
with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
    chatbot = build_chatbot(checkpointer)
    # Invoke or inspect while this connection remains open.
```
```bash
uv run 20_support_ticket_threads_sqlite.py
uv run 20_support_ticket_threads_sqlite.py --history <THREAD_A>
```
The actual receipt used the UUID printed by the first command; this public command replaces it with a placeholder.

```text
TITLE: 'Delayed headphones'
SAVED MESSAGE COUNT: 4
HumanMessage: My headphones are late.
AIMessage: Received: My headphones are late.
HumanMessage: My order ID is ORDER-EXAMPLE.
AIMessage: Received: My order ID is ORDER-EXAMPLE.
```
No node executed during the second command. The data was read from disk in another process. Titles saved in file 19 cannot retroactively recover the RAM-only messages from its old runs.

## Bappy's additional discovery method
```python
def get_all_threads(checkpointer):
    thread_ids = set()
    for record in checkpointer.list(None):
        thread_ids.add(record.config["configurable"]["thread_id"])
    return list(thread_ids)
```
list(None) iterates checkpoint records across threads, not one row per conversation. A set deduplicates repeated thread IDs; it does not preserve recency order. This mechanism was explained but not run as a separate lab. A directory can include an empty registered conversation and titles; checkpoint discovery sees histories with saved checkpoints.

## In production
The JSON file is a local teaching implementation, not a concurrent multi-user metadata store. Use a transactional conversation metadata table with ownership, timestamps, and titles when appropriate. A JSON write and a checkpoint write are not one atomic transaction. Automatic title generation remains optional and was not implemented.

## Interview questions
::: question Why not use only checkpoint.list(None) for the complete conversation directory?
It can discover saved thread IDs but does not automatically provide our custom titles, ownership model, or never-started conversations.
:::
::: question What did --history prove that the first run did not?
The checkpoint file could be reopened by a new process and recovered the same history without executing nodes.
:::

## References
- [Checkpointer listing](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- [Python JSON](https://docs.python.org/3.14/library/json.html)
