## What it is and why it matters
A collection of functions is not enough to specify which ones may run next or what state they receive. A graph makes that control flow explicit.

## Learn from the beginning
**Prerequisite:** Python functions that accept and return dictionaries. Your goal is to predict the state passed to each function before running a graph.

### Concept 1 — State is shared workflow data
A **state** is the data the workflow carries between steps. A **node** is a unit of work, usually a Python function. An **edge** says which node can run next. `START` marks the entry point; `END` marks termination of that execution path. They are graph sentinels, not customer messages or functions you implement.

```python
from typing import NotRequired, TypedDict

class State(TypedDict):
    ticket: str
    category: NotRequired[str]
```

`ticket` is expected input. `category` may be absent until classification runs. At runtime this state is still dictionary data. `TypedDict` does not automatically reject an invalid business value or create missing fields.

### Concept 2 — A node returns an update
```python
def classify(state: State) -> dict:
    return {"category": "delivery"}
```

The node reads `ticket` if needed and returns the keys it changes. LangGraph applies that update to state. It does not erase `ticket` merely because it was absent from the return value. Avoid mutating the input dictionary in place: explicit returned updates make state changes observable and compatible with graph execution.

Without a custom reducer, a new value replaces the old value for that key. A **reducer** is the rule used to combine existing data and updates; it is introduced in the parallel lesson. Independent keys do not need a reducer just because they share one dictionary.

### Concept 3 — Build, compile, and invoke are separate phases
```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_edge(START, "classify")
builder.add_edge("classify", END)
graph = builder.compile()
result = graph.invoke({"ticket": "My parcel is late."})
```

`StateGraph(State)` creates a builder with a state schema. `add_node` registers a name and callable; it does not run the function. `add_edge` registers a dependency. `compile()` checks graph structure and produces an executable graph. It does not ask an LLM to evaluate the workflow. `invoke()` runs it with actual input. `builder` is our variable name, not a required API called `build()`.

```text
Definition time: schema + callables + edges --> compile --> runnable graph
Execution time:  input state --> node update --> output state
```

Compilation can detect structural errors; it cannot prove a prompt correct or a remote API reachable. Keep construction outside a repeated conversation-turn loop so each turn invokes the same compiled graph and checkpointer.

## Build it in small pieces
Register one node first. Add START and END edges. Compile. Then invoke and print the state. The complete [graph core lab](../examples/04_graph_core.py) logs every phase and shows the input key surviving the node update.

A **super-step** is one graph scheduling round. Nodes scheduled in that round read the round's input state; their returned writes are applied at a boundary before dependent work sees them. Sequential nodes occupy separate rounds. More detail comes with parallelism.

## Check your understanding
Predict whether `ticket` remains after `classify` returns only `category`. Run the lab and paste the final dictionary.

::: question Exercise receipt: define versus execute
Add a print inside the node. Show whether it appears during add_node, compile, or invoke.
:::
::: question Exercise receipt: missing data
Read `state["category"]` before it has been produced. Paste the error type and explain why NotRequired did not create a default.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/04_graph_core.py). Run from the repository root:

```bash
uv run examples/04_graph_core.py
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

from typing import NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    ticket: str
    category: NotRequired[str]

def classify(state: State):
    log(f"classify START ticket={state['ticket']!r}")
    log("classify DONE category='delivery'")
    return {"category": "delivery"}

builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_edge(START, "classify")
builder.add_edge("classify", END)
log("COMPILE (node has not run)")
graph = builder.compile()

if __name__ == "__main__":
    log("INVOKE")
    result = graph.invoke({"ticket": "My parcel is late."})
    log(f"FINAL {result}")
    assert result == {"ticket": "My parcel is late.", "category": "delivery"}
```
:::

Author verification output (elapsed times vary):

```text
[  0.27s] COMPILE (node has not run)
[  0.27s] INVOKE
[  0.27s] classify START ticket='My parcel is late.'
[  0.27s] classify DONE category='delivery'
[  0.27s] FINAL {'ticket': 'My parcel is late.', 'category': 'delivery'}
```

| Trace observation | What it establishes |
| --- | --- |
| COMPILE appears before classify START | Registering and compiling did not execute the node. |
| FINAL contains ticket and category | A partial node update preserved the existing ticket key. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
add_node registers the callable, compile produces an executable graph, invoke runs it. Returning category does not remove ticket. NotRequired allows an absent key in the schema; subscripting an absent runtime key still raises KeyError.
:::

## Historical learner lab record

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

- [Graph API method reference](https://reference.langchain.com/python/langgraph/graphs)
