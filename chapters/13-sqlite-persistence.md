## What it is and why it matters
Restarting Python destroys RAM-only checkpoints. A SQLite checkpointer writes graph checkpoints to a local database file so another process can restore them later.

## Connection lifetime
```python
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

DB_PATH = Path(__file__).resolve().parent / "support_chatbot.sqlite"
with SqliteSaver.from_conn_string(str(DB_PATH)) as checkpointer:
    chatbot = builder.compile(checkpointer=checkpointer)
    result = chatbot.invoke(initial_state, config=chat_config)
    snapshot = chatbot.get_state(chat_config)
```
Keep invoke(), stream(), and saved-state access inside the connection's with block. The saver creates its required tables when needed; there is no need to manually create checkpoint tables.

## Labs: file 15
```bash
uv run python -c "from langgraph.checkpoint.sqlite import SqliteSaver; print('SQLite checkpointer ready')"
uv run 15_support_chatbot_sqlite.py
```
```text
SQLite checkpointer ready
DATABASE <PROJECT_ROOT>/support_ticket/support_chatbot.sqlite
You: My order ID is ORDER-EXAMPLE.
graph DONE messages=2
You: EXIT
```
Separate Python process:
```bash
uv run 15_support_chatbot_sqlite.py
```
```text
You: /history
SAVED HISTORY thread='support-demo-1' messages=2
1. HumanMessage: My order ID is ORDER-EXAMPLE.
2. AIMessage: Could you let me know what issue you’re experiencing with order ORDER-EXAMPLE?
```
The second process recovered both messages. The receipt proves persistence for this database file and thread ID.

## Serialization
**Serialization:** converting Python state into a storable representation. The saver serializes supported values and reconstructs them when loading checkpoints. It does not freeze the entire Python process or preserve arbitrary local variables.

## Mistakes and corrections
| Claim | Correction |
| --- | --- |
| A browser refresh always clears the server's RAM | It can reset a UI session; that is not the same as killing the Python process |
| check_same_thread=False enables multiple conversations | It concerns Python threads using a SQLite connection, not chat thread IDs |
| A .sqlite file makes deployment storage automatically durable | The file must be on storage retained by the hosting environment |
| A different relative working directory is harmless | It can select/create a different database file; resolve the path deliberately |

## In production
SQLite is suitable for these local synchronous labs. Choose a persistent backend appropriate for concurrency, operations, backup, and hosting requirements. JSON conversation metadata and checkpoint data are separate concerns even if both eventually live in PostgreSQL.

## Interview questions
::: question Does the checkpointer remember a function's local variables?
No. It saves graph state and execution/checkpoint information, not a suspended Python call stack.
:::
::: question Why can history appear empty after a successful save?
Check the database path, thread ID, process/storage lifetime, and whether you are reading the expected checkpoint.
:::

## References
- [SQLite checkpointer source](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py)
- [Python SQLite connections](https://docs.python.org/3.14/library/sqlite3.html#sqlite3.connect)
