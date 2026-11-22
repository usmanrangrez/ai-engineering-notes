## What it is and why it matters
A collection of functions is not enough to specify which ones may run next or what state they receive. A graph makes that control flow explicit.

| Term | Meaning in our labs |
| --- | --- |
| State | Shared named values described by a TypedDict |
| Node | Callable that performs work and usually returns a partial state update |
| Edge | Scheduling relationship between nodes |
| START / END | Entry and termination sentinels, not ordinary model calls |
| Super-step | One execution round of the graph; siblings can run concurrently |
| Reducer | Function used to combine updates to a state field |

## Build versus compile
```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    ticket: str

builder = StateGraph(State)
builder.add_node("process", process)
builder.add_edge(START, "process")
builder.add_edge("process", END)
graph = builder.compile()
result = graph.invoke({"ticket": "My parcel is late."})
```
The builder describes the graph. compile() validates and constructs the executable graph. invoke() executes it. Compiling does not call the model or process the ticket.

## Node update versus complete state
Returning `{"reply": text}` updates that key; the node does not need to return every existing field. Without a reducer, sequential updates normally replace the field's prior value. Concurrent writes to a single-value field are ambiguous and rejected.

## Lab evidence
The sequential lab ended with all input and derived keys present:
```text
[  0.90s] ■ graph DONE keys=['analysis', 'policy', 'reply', 'ticket']
```
The initial ticket survived while later nodes added analysis, policy, and reply.

## Mistakes and fixes
| Mistake | Correction |
| --- | --- |
| Expecting compile() to execute a node | Call invoke() or consume stream() to execute |
| Returning the entire state from every node | Return the intended update; avoid accidental duplicate reducer content |
| Treating all optional keys as always present | NotRequired means a key may not exist; schedule dependencies or guard reads |

## In production
Keep node boundaries aligned with meaningful units of work and recovery. Compilation checks graph structure, not all business invariants or correctness of the model's response.

## Interview questions
::: question Does compile() validate every possible state at runtime?
No. It constructs and validates the executable graph structure; a TypedDict is not a runtime domain validator.
:::
::: question What does a node normally return?
A dictionary of state updates. LangGraph applies field-specific reduction or replacement semantics.
:::

## References
- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
