## What it is and why it matters
An LLM by itself is a **closed text predictor**: its knowledge freezes at training time, it cannot query a live SQL database, cannot check real-time shipping status, and cannot trigger external APIs. **Tool calling** (also called function calling) turns an LLM from a passive text generator into an **action-selecting controller**: instead of guessing live facts, the model emits a structured JSON request asking your application to execute a specific, explicitly permitted Python function and return the real result.

::: mental-model Think of the LLM as a doctor writing a lab order, not the lab technician
The doctor (LLM) does not run the blood test itself. It writes a structured requisition form (`AIMessage.tool_calls`: test name + patient ID). Your lab (`ToolNode` + Python) runs the real test, stamps the result with the matching requisition ID (`ToolMessage.tool_call_id`), and hands it back so the doctor can explain the diagnosis to the patient.
:::

## First-principles theory: how tool calling actually works

### 1. From Python function to JSON Schema (`@tool` + `bind_tools`)
Modern chat models do **not** read your Python source code. When you decorate a function with `@tool` and call `llm.bind_tools(tools)`, LangChain inspects three things using Python introspection and compiles them into a **JSON Schema** sent inside the provider's HTTP API request:

1. **Function name** (`get_order_status`) → tells the model what identifier to emit.
2. **Type annotations** (`order_id: str`) → generates strict JSON parameter types (`{"type": "string"}`) and marks required fields.
3. **Docstring** (`"""Check shipping status for a customer order ID."""`) → tells the model *when* to choose this tool over answering directly or calling another tool.

::: warning Bad docstrings cause bad tool selection
Because the model only sees the name, parameter schema, and docstring, a vague docstring like `"""Helper function."""` causes missed or wrong tool calls. Write docstrings as decision rules: what the tool looks up, what format each argument expects, and when *not* to use it.
:::

### 2. The 4-step protocol across the wire
Step through the interactive protocol below to see the exact payloads exchanged between your Python process, LangGraph, and the LLM provider:

::: visual tool-calling-protocol | 4-step interactive trace of the tool-calling protocol

Notice the strict **message-role contract** enforced by every modern LLM API (Groq, OpenAI, Anthropic, Gemini):
- Every `AIMessage` with non-empty `tool_calls` **must** be followed immediately by a matching `ToolMessage` for *every* `id` in `tool_calls`.
- If a `ToolMessage` is missing, or its `tool_call_id` does not match `AIMessage.tool_calls[i]["id"]`, the provider rejects the next request with **HTTP 400**.
- A model can request **zero** tools (direct reply like `"Hello!"`), **one** tool, or **multiple parallel** tools in a single `AIMessage.tool_calls` list.

### 3. Why LangGraph needs `ToolNode`, `tools_condition`, and the back edge
In raw Python you would write `if response.tool_calls: ... else: ...` inside a manual loop. LangGraph turns that exact control flow into explicit graph components:

| Component | What it is | What it does at runtime |
| --- | --- | --- |
| `MessagesState` | State schema with `add_messages` reducer | Appends each `HumanMessage`, `AIMessage`, and `ToolMessage` into `state["messages"]` without overwriting history. |
| `ask_model` node | Your Python node calling `model_with_tools.invoke(...)` | Decides whether to answer directly (`tool_calls=[]`) or request tool(s). |
| `tools_condition` | Built-in conditional router function | Inspects the last message in `state["messages"]`: routes to `"tools"` if `tool_calls` is non-empty, else routes to `END`. |
| `ToolNode(tools)` | Built-in graph node executor | Loops over every entry in `AIMessage.tool_calls`, validates arguments, runs the matching Python `@tool`, and appends `ToolMessage(content=..., tool_call_id=...)`. |
| `tools → ask_model` | Back edge | Returns control to `ask_model` so the model reads the new `ToolMessage` and writes the final user-facing reply. |

::: concept Edges control execution order; state carries data
`ToolNode` does not "pass" the string directly as a Python function argument to `ask_model`. Instead, `ToolNode` returns `{"messages": [ToolMessage(...)]}` into `MessagesState`, and the edge `tools → ask_model` schedules `ask_model` next so it reads the updated `state["messages"]`.
:::

## Annotated code walkthrough

```python
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


# 1. Define a tool: name + type hints + docstring become the JSON Schema.
@tool
def get_order_status(order_id: str) -> str:
    """Look up the live shipping status for a customer order ID like ORD-42."""
    return {"ORD-42": "IN_TRANSIT"}.get(order_id, "ORDER_NOT_FOUND")


# 2. Bind tool schemas to the model (does NOT execute Python).
tools = [get_order_status]
llm = ChatGroq(model="openai/gpt-oss-120b", reasoning_effort="low", max_tokens=300)
model_with_tools = llm.bind_tools(tools)


# 3. Model node: prepend SystemMessage + existing conversation history.
def ask_model(state: MessagesState) -> dict:
    messages_for_model = [SystemMessage(content="Use tools for order lookups.")] + state["messages"]
    response = model_with_tools.invoke(messages_for_model)
    return {"messages": [response]}  # add_messages appends this AIMessage


# 4. Wire the graph: START -> ask_model -> (tools -> ask_model)* -> END.
builder = StateGraph(MessagesState)
builder.add_node("ask_model", ask_model)
builder.add_node("tools", ToolNode(tools))  # "tools" is the node name; ToolNode executes Python

builder.add_edge(START, "ask_model")
builder.add_conditional_edges("ask_model", tools_condition)
builder.add_edge("tools", "ask_model")

graph = builder.compile()
```

## Historical learner lab record
File: `<PROJECT_ROOT>/support_ticket/24_support_ticket_tools.py` (aligned with DSwithBappy Video 19 / Chatbot Part 7; Bappy demonstrates stock-price/calculator tools while our lab applied the exact pattern to support-ticket order lookup).

Verified stages completed hands-on:
1. Defined `@tool` (`get_order_status`) and invoked it manually with an argument dictionary (`{"order_id": "ORD-42"}`).
2. Bound the tool with `bind_tools`, inspected `AIMessage.tool_calls`, executed the requested call to obtain `IN_TRANSIT`, and manually constructed a `ToolMessage` with matching `tool_call_id` for the second model call.
3. Replaced the manual loop with `ToolNode(tools)`, `tools_condition`, and the `tools → ask_model` back edge.

Observed routing receipts:
- **Greeting prompt (`"Hi"`):** `0` tool calls → `['HumanMessage', 'AIMessage']` → routed straight to `END`.
- **Order prompt (`ORD-42`):** `1` tool call (`get_order_status`) → `ToolMessage('IN_TRANSIT')` → second model call → `['HumanMessage', 'AIMessage', 'ToolMessage', 'AIMessage']`.

## Mistakes and fixes
- **Forgetting the back edge (`tools → ask_model`):** without returning to `ask_model`, the graph terminates immediately after `ToolNode` and exposes a raw `ToolMessage` instead of a user-facing answer.
- **Confusing graph node name with Python function name:** in `builder.add_node("tools", ToolNode(tools))`, `"tools"` is the graph node name expected by `tools_condition`; `ToolNode(tools)` dispatches to the decorated Python functions inside `tools`.

## In production
::: tip Production safety boundary for tools
Treat every model-generated tool argument as **untrusted user input**. Validate types and ranges with Pydantic, scope database queries by authenticated user ID (never trust an LLM-supplied `user_id` without checking authorization), return concise error strings instead of stack traces inside `ToolMessage`, and gate write/money-moving tools behind Human-in-the-Loop approval (Chapter 24).
:::

## Interview questions
::: question Does `llm.bind_tools(tools)` execute Python code or send Python source code to the LLM?
Neither. `bind_tools` converts each tool's name, type annotations, and docstring into a JSON Schema attached to the API request. The model only returns structured JSON inside `AIMessage.tool_calls`; your application (`ToolNode`) executes the Python function.
:::
::: question Why must `ToolMessage.tool_call_id` match `AIMessage.tool_calls[i]["id"]`?
LLM APIs require a strict 1-to-1 correspondence between every requested tool call ID and its returned `ToolMessage` so the model knows which result belongs to which request—especially when multiple tool calls are issued in parallel in one turn.
:::
::: question What happens if you omit `builder.add_edge("tools", "ask_model")`?
Execution stops after `ToolNode` appends the `ToolMessage`. The model never gets a second turn to read the tool result and synthesize a grounded reply.
:::

## References
- [LangChain tools documentation](https://docs.langchain.com/oss/python/langchain/tools)
- [DSwithBappy Part 7 video](https://www.youtube.com/watch?v=pkwVn8ZtRvE)
- [Course repository](https://github.com/entbappy/Complete-Agentic-AI-Course)
