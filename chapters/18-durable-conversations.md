## What it is and why it matters
Saving checkpoint state is insufficient if the application forgets which conversation IDs exist. Conversely, restoring a directory of titles does not restore RAM-only messages. Persist both responsibilities.

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
