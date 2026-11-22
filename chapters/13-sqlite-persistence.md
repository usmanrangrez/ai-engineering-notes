## What it is and why it matters
Restarting Python destroys RAM-only checkpoints. A SQLite checkpointer writes graph checkpoints to a local database file so another process can restore them later.

## Learn from the beginning
**Prerequisite:** in-memory checkpointing. Your goal is to demonstrate persistence across two separate Python processes, rather than just between two calls in one process.

### Concept 1 — Durable storage outlives process memory
**Durable** means data remains available after the process stops, subject to the storage system's guarantees. **SQLite** is a database engine that stores data in a file without requiring a separate database server. `SqliteSaver` implements LangGraph checkpoint storage using SQLite.

```text
Process 1 --> checkpointer --> database file
                                      |
Process 2 --> same database file + same thread ID --> saved conversation
```

Both the path and thread ID must match. Creating a new database in a different working directory can look like memory loss even though the old file still exists. Using a new ID with the same file correctly selects a different conversation.

### Concept 2 — Keep the storage connection alive
```python
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver

path = Path(__file__).resolve().parent / "data" / "learning.sqlite"
path.parent.mkdir(parents=True, exist_ok=True)
with SqliteSaver.from_conn_string(str(path)) as checkpointer:
    chatbot = builder.compile(checkpointer=checkpointer)
    result = chatbot.invoke(new_message_state, config=chat_config)
    snapshot = chatbot.get_state(chat_config)
```

A **connection** is the handle the code uses to communicate with the database. A **context manager**, the `with` block, manages its lifetime and cleanup. Keep invocations and reads inside it. A graph object escaping the block does not keep an already-closed connection usable.

`__file__` identifies the current script; `resolve().parent` anchors the database to that script rather than the terminal's current directory. `mkdir(..., exist_ok=True)` creates the data directory if missing without treating an existing directory as an error. The optional SQLite package is installed separately from core LangGraph.

### Concept 3 — Serialization makes Python values storable
**Serialization** converts a Python object into a representation that can be saved or transmitted. **Deserialization** rebuilds a usable representation from saved data. Message objects are not simply written as live Python pointers. The checkpointer's serializer handles supported state values so a later process can restore them.

This does not make every object a good state value. Keep connections, model clients, file handles, and other runtime resources outside saved state. Store data such as message content, counters, and identifiers. Changing schemas later requires compatibility planning; persistence is not an exemption from data modeling.

## Build it in small pieces
The [offline SQLite lab](../examples/13_sqlite.py) has `--write` and `--read` modes. Write once, let the process exit, then read in a fresh process. It uses a temporary-file location by default so it does not touch your existing conversation database. Pass an explicit path to inspect your own test file.

First predict whether `--read` will trigger a node. It should only call get_state, so its output is a saved count, not another generated answer. Repeat with a fresh thread ID to distinguish missing history from a database problem.

## Local durability is not every production requirement
A file in an ephemeral container can disappear when the container is replaced even though Python closed it cleanly. SQLite also has concurrency/operational characteristics different from a managed PostgreSQL deployment. Choose storage for expected load, locking, backups, isolation, and deployment topology; do not infer that using SQL alone makes an application scalable.

::: question Exercise receipt: prove restart persistence
Run write and read as two separate commands. Paste the final message count from each and the same database path with personal details replaced.
:::
::: question Exercise receipt: identify a path bug
Run from another working directory. Does a path based on __file__ change? Explain the difference from using a bare relative filename.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/13_sqlite.py). Run from the repository root:

```bash
uv run examples/13_sqlite.py --write
uv run examples/13_sqlite.py --read
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

import argparse
import tempfile
from pathlib import Path
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat(state):
    log(f"chat START messages={len(state['messages'])}")
    return {"messages": [AIMessage(content="What happened to the delivery?")]}

builder = StateGraph(State)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--read", action="store_true")
    parser.add_argument("--db", type=Path, default=Path(tempfile.gettempdir()) / "ai-notes-sqlite-demo.sqlite")
    parser.add_argument("--thread", default="sqlite-demo")
    args = parser.parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": args.thread}}
    with SqliteSaver.from_conn_string(str(args.db)) as saver:
        chatbot = builder.compile(checkpointer=saver)
        if args.write:
            chatbot.invoke({"messages": [HumanMessage(content="My order ID is ORDER-EXAMPLE.")]}, config=config)
        messages = chatbot.get_state(config).values.get("messages", [])
        log(f"SAVED messages={len(messages)}")
        for message in messages:
            print(type(message).__name__, message.content)
```
:::

Author verification output (elapsed times vary):

```text
[  0.24s] chat START messages=1
[  0.24s] SAVED messages=2
HumanMessage My order ID is ORDER-EXAMPLE.
AIMessage What happened to the delivery?
[  0.23s] SAVED messages=2
HumanMessage My order ID is ORDER-EXAMPLE.
AIMessage What happened to the delivery?
```

| Trace observation | What it establishes |
| --- | --- |
| SAVED messages=2 appears in each process | The reader restored the written state after the writer exited. |
| Only the writer prints chat START | Reading the saved state did not execute the chat node. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Both the database path and the thread ID must match across processes. The database connection must remain open during graph access. A stable path based on __file__ avoids accidental changes caused by the terminal working directory.
:::

## Historical learner lab record

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
