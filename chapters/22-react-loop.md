## What it is and why it matters
Real tasks often need more than one tool call in sequence—where the output of Tool 1 becomes the input to Tool 2. Building an explicit ReAct-style loop in LangGraph shows how a model observes a tool result, decides on a dependent follow-up call, and stops cleanly under an application tool budget.

## Learn from the beginning
**Prerequisite:** single-tool calling with `ToolNode` and `tools_condition` from chapter 21.

### Concept 1 — ReAct is a repeated Reason → Act → Observe cycle
In a ReAct loop, the same graph structure (`START → ask_model → tools_condition → tools → ask_model`) handles multi-step reasoning without hardcoding the number of steps:

```text
HumanMessage ("What is the shipment status of order ORD-42?")
  ─▶ ask_model (#1): requests get_tracking_number("ORD-42")
  ─▶ ToolNode:       returns ToolMessage("TRK-8317")
  ─▶ ask_model (#2): reads "TRK-8317", requests get_shipment_status("TRK-8317")
  ─▶ ToolNode:       returns ToolMessage("IN_TRANSIT")
  ─▶ ask_model (#3): reads "IN_TRANSIT" (tools_enabled=False), writes final answer
  ─▶ tools_condition ─▶ END
```

### Concept 2 — Dependent tools pass real values through state
Notice that `"TRK-8317"` is never hardcoded into the second prompt. The graph state (`MessagesState`) carries the first `ToolMessage` back into `ask_model`, and the chat model extracts `"TRK-8317"` to form the argument for `get_shipment_status`.

### Concept 3 — Separate application tool budget from `recursion_limit`
`recursion_limit` is a runtime safety net that raises `GraphRecursionError` when a graph loops too far. An **application tool budget** (counting `ToolMessage` items in `state["messages"]` and switching from `model_with_tools` to the plain `llm` once `used >= MAX_TOOL_CALLS`) gives a clean, normal stop where the model still summarizes what it found.

```python
used = sum(isinstance(message, ToolMessage) for message in messages)
can_call_tools = used < MAX_TOOL_CALLS
model = model_with_tools if can_call_tools else llm
```

## Historical learner lab record
File: `<PROJECT_ROOT>/support_ticket/25_support_ticket_react.py` (application of DSwithBappy Part 7's stock-price → calculator chain to support-ticket tracking number → shipment status).

Observed live learner receipt:
- Prompt: `"What is the shipment status of order ORD-42?"`
- Tool chain executed: `ORD-42` → `get_tracking_number` returned `TRK-8317` → `get_shipment_status` received the exact returned `TRK-8317` and returned `IN_TRANSIT`.
- Model call counts: 3 model calls requesting `1`, `1`, and `0` tools.
- At the 3rd model call (`used = 2/2`), `tools_enabled=False`, so the graph invoked the plain chat model and returned the final answer cleanly.
- Resulting `MESSAGE TYPES`:
```text
['HumanMessage', 'AIMessage', 'ToolMessage', 'AIMessage', 'ToolMessage', 'AIMessage']
```

## Mistakes and fixes
- **Relying only on `recursion_limit` to stop loops:** hitting `recursion_limit` crashes the run with `GraphRecursionError` instead of producing a helpful final reply. Combining an explicit `MAX_TOOL_CALLS` policy with `recursion_limit` handles both normal completion and runaway failure.

## In production
Bound every agent loop with explicit tool budgets, per-call timeouts (`timeout=30`), limited retries (`max_retries=1`), and clear instructions forbidding fabricated tool data when a lookup returns not-found.

## Interview questions
::: question Why did the graph need 3 model calls to run 2 dependent tools?
Call 1 chooses the first tool (`get_tracking_number`), Call 2 reads `TRK-8317` and chooses the second tool (`get_shipment_status`), and Call 3 reads `IN_TRANSIT` and writes the final user-facing answer with 0 tool calls.
:::
::: question What is the difference between `MAX_TOOL_CALLS` and LangGraph's `recursion_limit`?
`MAX_TOOL_CALLS` is an application-level policy that disables tool binding so the model can finish normally with a reply; `recursion_limit` is a hard runtime ceiling that aborts execution with `GraphRecursionError`.
:::

## References
- [LangGraph workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [DSwithBappy Part 7 video](https://www.youtube.com/watch?v=pkwVn8ZtRvE)
- [Course repository](https://github.com/entbappy/Complete-Agentic-AI-Course)
