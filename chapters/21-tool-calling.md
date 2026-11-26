## What it is and why it matters
A chat model alone can only generate text from its training data and the prompt—it cannot look up live order records or run Python functions by itself. Tool calling lets the model request a specific Python operation by name and arguments, receive the real result in a `ToolMessage`, and answer from verified data instead of guessing.

## Learn from the beginning
**Prerequisite:** `MessagesState` and `add_messages` from chapter 11. Your goal is to trace a single tool request from the model through execution and back to a final answer.

### Concept 1 — `bind_tools` advertises tools; it does not run them
Decorating a Python function with `@tool` creates a LangChain tool with a **name**, **argument schema** (from its Python type hints), and **docstring**. Calling `llm.bind_tools(tools)` sends those descriptions to the model provider so the model knows what it may request.

```text
User prompt ─▶ model_with_tools.invoke(messages)
                     │
                     ├─ No tool needed ─▶ AIMessage(content="Hello!", tool_calls=[])
                     └─ Tool needed    ─▶ AIMessage(content="", tool_calls=[{name, args, id}])
```

The model never executes Python directly. It only returns a structured request inside `AIMessage.tool_calls`.

### Concept 2 — `ToolMessage.tool_call_id` links each result to its request
After Python runs the requested tool function, the result must be wrapped in a `ToolMessage` whose `tool_call_id` matches the `id` from `AIMessage.tool_calls`. On the second model call, the model reads the full conversation—original `HumanMessage`, requesting `AIMessage`, and matching `ToolMessage`—and writes the final user-facing reply.

### Concept 3 — `ToolNode` and `tools_condition` automate the loop
Instead of writing manual `if response.tool_calls:` branches, LangGraph supplies two prebuilt pieces:
- **`ToolNode(tools)`** is registered as a normal graph node (`builder.add_node("tools", ToolNode(tools))`). It reads `AIMessage.tool_calls`, executes the matching Python tool, and appends a `ToolMessage` to `state["messages"]`.
- **`tools_condition`** is a conditional routing function after the model node: if the last `AIMessage` has non-empty `tool_calls`, route to `"tools"`; otherwise route to `END`.
- **Back edge (`tools → model`)** returns control to the model node so it can read the `ToolMessage` and answer.

## Historical learner lab record
File: `<PROJECT_ROOT>/support_ticket/24_support_ticket_tools.py` (aligned with DSwithBappy Video 19 / Chatbot Part 7; Bappy's notebook demonstrates stock-price/calculator tools while our lab applied the exact same pattern to support-ticket order lookup).

Verified stages completed hands-on:
1. Defined `@tool` order lookup (`get_order_status`) and called it directly with an argument dictionary.
2. Bound the tool with `bind_tools`, inspected the requesting `AIMessage.tool_calls`, executed the requested lookup to obtain `IN_TRANSIT`, and returned a `ToolMessage` with matching `tool_call_id` for the second model call.
3. Replaced manual execution with `ToolNode(tools)`, `tools_condition`, and the `tools → model` back edge.

Observed routing behavior:
- **Greeting prompt:** `0` tool calls; routed straight to `END`.
- **Order lookup (`ORD-42`):** `1` tool call (`get_order_status`) → `ToolMessage` (`IN_TRANSIT`) → second model call → grounded reply.

## Mistakes and fixes
- **Forgetting the back edge (`tools → model`):** without the edge returning from `"tools"` to the model node, the graph stops at a raw `ToolMessage` instead of generating a user-facing reply.
- **Confusing node name with executor:** in `builder.add_node("tools", ToolNode(tools))`, `"tools"` is the graph node name, `ToolNode(tools)` is the executor wrapper, and the decorated Python function runs inside it.

## In production
Validate tool arguments strictly, keep tool descriptions narrow and accurate, and never expose destructive operations (refunds, writes, emails) without authorization or human-in-the-loop approval.

## Interview questions
::: question Does `llm.bind_tools(tools)` execute Python code?
No. `bind_tools` only attaches tool schemas (names, parameters, docstrings) to model requests. The model returns a structured `tool_calls` request; your application or LangGraph's `ToolNode` executes the Python function.
:::
::: question Why must `ToolMessage.tool_call_id` match `AIMessage.tool_calls[i]["id"]`?
Chat APIs require every tool output to correspond to a specific pending tool request ID so the model can pair results accurately—especially when multiple tool calls occur in one turn.
:::

## References
- [LangChain tools documentation](https://docs.langchain.com/oss/python/langchain/tools)
- [DSwithBappy Part 7 video](https://www.youtube.com/watch?v=pkwVn8ZtRvE)
- [Course repository](https://github.com/entbappy/Complete-Agentic-AI-Course)
