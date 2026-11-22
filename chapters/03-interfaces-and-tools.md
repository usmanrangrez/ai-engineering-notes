## What it is and why it matters
A model wrapper, a tool, and a graph can all expose `invoke()`. The shared method name does not mean they perform the same work.

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
