## What it is and why it matters
A model wrapper, a tool, and a graph can all expose `invoke()`. The shared method name does not mean they perform the same work.

::: concept Clear separation of the 4 ecosystem layers
- **Model provider (Groq, Google, OpenAI):** hosts neural network inference over HTTP.
- **LangChain (`langchain-core`):** standardizes models, messages (`HumanMessage`/`AIMessage`), `@tool` schemas, and the `Runnable` interface.
- **LangGraph:** orchestrates stateful control flow—nodes, edges, cycles, checkpoints, streaming, and `interrupt()`.
- **LangSmith:** observes, traces, and evaluates runs without changing application control flow.
:::

::: warning Calling `tool.invoke(...)` directly is NOT an agent
When your Python code calls `lookup_policy.invoke({"category": "delivery"})`, *your code* chose the tool. In an agent (Chapters 21–22), the **LLM** requests the tool via `AIMessage.tool_calls`, and your runtime validates and executes it.
:::

## Learn from the beginning
**Prerequisite:** chapter 2's distinction between annotations and runtime validation. Your goal is to identify who chooses an operation, who executes it, and what a returned object contains.

### Concept 1 — The model and the tool are different objects
An **LLM** is a model accessed through an inference service: it predicts a response from supplied input. A **tool** is an operation your application exposes, such as looking up a policy. The model can request a tool call, but your runtime must validate and execute that request. The model itself is not your Python function.

```text
Python directly calls lookup_policy --> policy string
Model requests lookup_policy -------> runtime executes --> tool result --> model
```

Our early sequential lab used the first shape. It demonstrated calling a tool object; it did not yet implement an autonomous agent loop. Tool calling as a graph is a later chapter.

### Concept 2 — invoke belongs to the object receiving it
The same method name does not imply identical inputs or return values.

| Expression | What is invoked | Typical result here |
| --- | --- | --- |
| `chat_model.invoke(messages)` | A model request | AIMessage |
| `structured_model.invoke(messages)` | Model request plus parsing | Pydantic Evaluation |
| `lookup_policy.invoke(arguments)` | A tool operation | Policy string |
| `graph.invoke(state)` | Compiled workflow | Final output-state dictionary |

An **AIMessage** is a message object containing generated content and associated metadata. A **runnable** is LangChain's common execution interface for components that can be invoked or composed. Read the actual object's contract rather than guessing from the method name.

### Concept 3 — A dictionary supplies named arguments
```python
from typing import Literal
from langchain_core.tools import tool

@tool
def lookup_policy(category: Literal["refund", "delivery"]) -> str:
    """Look up the support policy for a known issue category."""
    policies = {
        "refund": "Verify the order before discussing eligibility.",
        "delivery": "Ask for the order ID and check tracking.",
    }
    return policies[category]

policy = lookup_policy.invoke({"category": "delivery"})
```

The decorator turns the function into a tool object with a name, description, and input schema. The key `category` matches the parameter name. The value `"delivery"` is the argument checked against the schema. The argument is not the whole dictionary passed into the `category` variable. Conceptually, validation is followed by calling the underlying function with `category="delivery"`.

## Framework roles without the slogans
LangChain provides model, message, tool, prompt, and runnable integrations. LangGraph coordinates state and control flow across operations. LangSmith records execution and supports evaluation. A model provider hosts inference. These products have separate jobs even when packages install one another as dependencies.

For a fixed three-function transformation, ordinary Python may be enough. Use an orchestration framework when explicit branching, saved execution, recovery, inspection, or composition justify its operational cost. A graph containing an LLM is not automatically an agent: the interesting question is who controls the next action.

## Check your understanding
Before executing the snippet, predict the return type and whether `category="billing"` will be accepted by this tool schema. The [offline tool lab](../examples/03_tools.py) provides both cases.

::: question Exercise receipt: inspect the operation
Print `lookup_policy.name` and `lookup_policy.args`. Paste the field name and allowed values; do not paste any service keys.
:::
::: question Exercise receipt: locate the decision
In our sequential policy lookup, did the model request the tool directly, or did a Python node decide which tool to invoke? Answer with the calling line.
:::


## Runnable example and verified trace

Offline lab (no API key or model call required; [setup guide](../start.html)):

[Open the complete Python file](../examples/03_tools.py). Run from the repository root:

```bash
uv run examples/03_tools.py
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

from typing import Literal
from langchain_core.tools import tool
from pydantic import ValidationError

@tool
def lookup_policy(category: Literal["refund", "delivery"]) -> str:
    """Look up a policy for a known support category."""
    return {"refund": "Verify the order.", "delivery": "Ask for the order ID."}[category]

if __name__ == "__main__":
    log(f"TOOL {lookup_policy.name} ARGS {lookup_policy.args}")
    result = lookup_policy.invoke({"category": "delivery"})
    log(f"POLICY {result}")
    assert result == "Ask for the order ID."
    try:
        lookup_policy.invoke({"category": "billing"})
    except ValidationError as error:
        log(f"REJECTED {error.errors()[0]['type']}")
    else:
        raise AssertionError("Unknown category was accepted")
```
:::

Author verification output (elapsed times vary):

```text
[  0.30s] TOOL lookup_policy ARGS {'category': {'enum': ['refund', 'delivery'], 'title': 'Category', 'type': 'string'}}
[  0.31s] POLICY Ask for the order ID.
[  0.31s] REJECTED literal_error
```

| Trace observation | What it establishes |
| --- | --- |
| POLICY prints Ask for the order ID | The dictionary argument was validated and passed into the tool. |
| REJECTED literal_error | The tool schema rejected an unsupported category before lookup. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
The decorated tool receives category="delivery" after input validation. A direct invoke is selected by application code; it is not evidence that an LLM requested the operation. Model-message output and tool-string output have different types.
:::

## Historical learner lab record

| Object | Typical input | What happens |
| --- | --- | --- |
| Chat model | String or messages | Requests a model response |
| Structured model runnable | Prompt/messages | Calls a model and validates/parses the contract |
| LangChain tool | Argument dictionary | Validates and executes a callable |
| Compiled graph | State input and optional config | Executes scheduled nodes and merges their updates |

## The dictionary and Literal question
```python
@tool
def lookup_policy(
    category: Literal["refund", "delivery", "account", "other"]
) -> str:
    """Return the support policy for a category."""
    return policies[category]

policy = lookup_policy.invoke({"category": "refund"})
```
The tool wrapper reads the dictionary key `category`, validates the argument against its schema, and calls the underlying function. The function receives the string `"refund"`. `Literal` is the allowed-value constraint, not the mechanism that reads a dictionary.

## Lab receipt
```text
TOOL: lookup_policy
POLICY: Customers may request a refund within 30 days of delivery for defective products. Ask for the order ID and a description of the defect. Refund approval requires order verification.
```
The policy is demo data, not a real retailer's verified terms.

## Framework roles
LangChain provides model/tool abstractions and agent building blocks. LangGraph provides explicit stateful orchestration. LangSmith records instrumented execution for inspection. A workflow may use them together; LangGraph does not require LangChain for every operation.

## Mistakes and fixes
The statement “chains are stateless; graphs are stateful” was an introductory simplification. State and memory can be added around many architectures. The reason we use LangGraph is explicit control over execution, state transitions, cycles, and resumption.

A sequential graph can call LLMs and tools. Workflow shape describes dependencies, not what kinds of operations are allowed inside nodes. Explicitly executing lookup_policy is not yet the model choosing a tool call; that dedicated agent loop is the next lesson.

## In production
Keep tool execution, model suggestions, and business authorization separate. Passing a schema does not authorize an external action. Direct API tools and MCP are integration choices, not replacements for permissions.

## Interview questions
::: question Does a model execute Python when it produces a tool call?
No. It requests an operation with arguments. Application code decides whether and how to execute it.
:::
::: question Can a fixed sequential workflow contain an LLM?
Yes. Its node order can be fixed while a node internally calls a probabilistic model.
:::

## References
- [LangChain tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
