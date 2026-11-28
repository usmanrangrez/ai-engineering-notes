## What it is and why it matters
Single-tool calling breaks down as soon as a task requires **multi-hop reasoning**, where you do not know the input to Tool 2 until you inspect the output of Tool 1 (for example: you cannot look up a shipment status until you first look up the order's tracking number). A **ReAct (Reason + Act) loop** lets the model alternate between reasoning over accumulated observations and calling the next tool until it has enough evidence—or reaches an explicit safety budget.

## First-principles theory: the Reason → Act → Observe loop

### 1. Why single-shot prompting fails on dependent tasks
Consider the prompt: *"What is the shipment status of order ORD-42?"*
- `get_tracking_number(order_id)` returns `"TRK-8317"`.
- `get_shipment_status(tracking_number)` requires `"TRK-8317"`, which does **not** exist in the user's prompt.

A fixed 1-step pipeline cannot invent `"TRK-8317"`. Instead, the ReAct pattern (Yao et al., 2022) interleaves **Thought (Reason)** → **Action (Tool Call)** → **Observation (`ToolMessage`)** in a cycle backed by `MessagesState`. Each new `ToolMessage` becomes part of the next LLM prompt, letting the model dynamically extract `"TRK-8317"` and decide its next action at runtime.

::: visual react-loop-trace | 5-step interactive ReAct loop trace (ORD-42 → TRK-8317 → IN_TRANSIT)

### 2. Why 2 dependent tools require 3 LLM calls
A common beginner confusion is expecting 2 tools to take 2 model calls. Count the actual decision points:
1. **Model Call #1:** Reads `HumanMessage` → decides to call Tool 1 (`get_tracking_number("ORD-42")`).
2. **Model Call #2:** Reads `ToolMessage("TRK-8317")` → extracts `TRK-8317` and decides to call Tool 2 (`get_shipment_status("TRK-8317")`).
3. **Model Call #3:** Reads `ToolMessage("IN_TRANSIT")` → emits `tool_calls=[]` and writes the final grounded answer.

In general, a chain of `N` sequential tool calls requires **`N + 1` model calls** and produces **`2N + 2` messages** (`1 Human + N requesting AI + N Tool + 1 final AI`).

### 3. Termination theory: Application Tool Budget vs. `recursion_limit`
An unbounded loop is the #1 reliability hazard of ReAct agents: if a tool returns `"NOT_FOUND"` or ambiguous data, an LLM may retry the same broken call indefinitely, burning tokens and latency.

Production agents separate **two distinct stopping mechanisms**:

| Mechanism | Who enforces it | What happens when hit | Purpose |
| --- | --- | --- | --- |
| **Application Tool Budget (`MAX_TOOL_CALLS`)** | Your `ask_model` node (counts `ToolMessage`s and switches to plain `llm` without tools) | **Graceful finish:** model cannot call more tools, so it summarizes what it found so far and exits cleanly via `END`. | Normal business policy & cost control. |
| **Runtime `recursion_limit`** | LangGraph runtime (`config={"recursion_limit": 25}`) | **Hard crash:** raises `GraphRecursionError` immediately. | Last-resort safety net against bugs or infinite cycles. |

::: warning Never rely solely on `recursion_limit` for normal stopping
If you let `recursion_limit` stop a chatty agent, the user gets an unhandled exception instead of an answer. Use a tool budget (`can_call_tools = used < MAX_TOOL_CALLS`) for graceful degradation, and keep `recursion_limit` as the crash guard underneath.
:::

### 4. Common ReAct failure modes
1. **Hallucinated tool arguments:** Model invents a tracking number like `"TRK-0000"` instead of calling `get_tracking_number` first. *Fix:* clear system instructions + strict tool validation returning explicit `"ORDER_NOT_FOUND"` / `"TRACKING_NOT_FOUND"` tokens.
2. **Repeated failing calls (spin loop):** Model calls the same tool with the same bad argument repeatedly. *Fix:* enforce `MAX_TOOL_CALLS` and instruct the model to report missing data rather than retrying blindly.
3. **Context window bloat:** Every `ToolMessage` stays in `state["messages"]` for all subsequent calls. *Fix:* keep tool return strings concise and structured rather than dumping raw 50KB JSON payloads.

## Annotated code walkthrough (from `25_support_ticket_react.py`)

```python
MAX_TOOL_CALLS = 2

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    reasoning_effort="low",
    max_tokens=300,
    max_retries=1,
    timeout=30,
)
model_with_tools = llm.bind_tools(tools)


def ask_model(state: MessagesState) -> dict:
    messages = state["messages"]

    # Count how many tool results already exist in this run.
    used = sum(isinstance(message, ToolMessage) for message in messages)
    can_call_tools = used < MAX_TOOL_CALLS

    # Graceful budget: drop tool bindings once MAX_TOOL_CALLS is reached.
    model = model_with_tools if can_call_tools else llm

    response = model.invoke([SystemMessage(content=system_instruction), *messages])
    return {"messages": [response]}
```

Notice why the graph wiring (`START → ask_model → tools_condition → tools → ask_model`) is **100% identical** to Chapter 21. You do not add new nodes or edges for multi-hop reasoning—the loop itself handles `0`, `1`, `2`, ..., `MAX_TOOL_CALLS` hops dynamically!

## Historical learner lab record
File: `<PROJECT_ROOT>/support_ticket/25_support_ticket_react.py` (application of DSwithBappy Part 7's stock-price → calculator chain to support-ticket tracking number → shipment status).

Observed live learner receipt:
- Prompt: `"What is the shipment status of order ORD-42?"`
- Dependent chain executed: `ORD-42` → `get_tracking_number` returned `TRK-8317` → `get_shipment_status` received the exact returned `TRK-8317` and returned `IN_TRANSIT`.
- Model calls: **3 calls** requesting `1`, `1`, and `0` tools.
- On Call #3 (`used = 2/2`), `tools_enabled=False`, so the graph invoked the plain `llm` and returned the final reply cleanly.
- Resulting `MESSAGE TYPES` (`2N + 2 = 6` messages):
```text
['HumanMessage', 'AIMessage', 'ToolMessage', 'AIMessage', 'ToolMessage', 'AIMessage']
```

## In production
::: tip Prefer explicit graphs for fixed pipelines; use ReAct only when control flow must be dynamic
If every request *always* runs Step A → Step B → Step C in a fixed order, a deterministic sequential graph (Chapter 5) is faster, cheaper, and 100% predictable (0 extra LLM routing calls). Reach for a ReAct loop only when the number or order of tools genuinely depends on the user's request or intermediate tool outputs.
:::

## Interview questions
::: question Why did 2 dependent tool calls require 3 LLM calls and produce 6 messages?
Call 1 selects `get_tracking_number`; Call 2 observes `TRK-8317` and selects `get_shipment_status`; Call 3 observes `IN_TRANSIT` and generates the final user-facing reply with 0 tool calls. Total messages: `1 Human + 2 requesting AI + 2 Tool + 1 final AI = 6`.
:::
::: question What is the difference between `MAX_TOOL_CALLS` and LangGraph's `recursion_limit`?
`MAX_TOOL_CALLS` is an application-level policy that disables `bind_tools` so the model finishes gracefully with a summary reply. `recursion_limit` is a hard runtime step cap that aborts execution with `GraphRecursionError`.
:::
::: question When should you choose a deterministic workflow over a ReAct agent loop?
Choose a deterministic graph whenever the execution sequence is known ahead of time (lower latency, lower token cost, no risk of missed/wrong tool choices). Use ReAct when the agent must dynamically choose tools based on user intent or intermediate observations.
:::

## References
- [LangGraph workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al.)](https://arxiv.org/abs/2210.03629)
- [DSwithBappy Part 7 video](https://www.youtube.com/watch?v=pkwVn8ZtRvE)
- [Course repository](https://github.com/entbappy/Complete-Agentic-AI-Course)
