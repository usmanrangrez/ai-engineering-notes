## What it is and why it matters
Agents should run harmless read-only tools automatically, but sensitive or irreversible actions—issuing a refund, buying stock, sending an external email—need a human checkpoint before executing. **Human-in-the-Loop (HITL)** pauses a LangGraph workflow at `interrupt()`, persists state to a checkpointer, and resumes later with `Command(resume=...)` once a reviewer approves, edits, or rejects the action.

## Learn from the beginning
**Prerequisite:** tool calling (`ToolNode` and `tools_condition`) from chapters 21–22 and checkpointers from chapter 12.

### Concept 1 — Four real-world HITL patterns
- **Approve / Reject:** pause right before a sensitive action executes (refunds, stock purchases, outbound emails).
- **Review & Edit:** let a human modify the proposed arguments before executing (e.g., revising a `$120` refund down to `$50`).
- **Clarify ambiguity:** pause when the request is underspecified (*"This Friday or next Friday?"*).
- **Escalate:** transfer an edge-case conversation to a human operator.

### Concept 2 — Why LangGraph uses `interrupt()` instead of Python `input()`
Plain Python `input()` freezes the running process until someone types into a terminal. In a web backend, a reviewer might click **Approve** minutes or hours later—you cannot hold an HTTP request open that long.

::: visual hitl-vs-input | Side-by-side comparison of blocking Python input() vs. checkpointed LangGraph interrupt()

LangGraph's `interrupt(payload)` requires a **checkpointer** (`InMemorySaver` for local tests, `SqliteSaver` / Postgres for durable restarts) and a `thread_id`. When hit, LangGraph saves the paused checkpoint and exits `graph.invoke(...)` cleanly with the payload inside `result["__interrupt__"]`.

### Concept 3 — Pause inside the sensitive tool, not on every chat turn
Putting `interrupt()` inside `ask_model` would interrupt greetings and read-only lookups. Instead, put `interrupt()` **only inside sensitive `@tool` functions** (`issue_refund`), leaving safe tools (`get_order_status`) interrupt-free.

Step through all 4 frames below and test **Approve (`$120`)**, **Edit (`$50`)**, and **Reject**:

::: visual hitl-pause-resume | Interactive 4-frame HITL walkthrough showing Approve, Edit, and Reject via Command(resume=...)

### Concept 4 — Two critical runtime rules
1. **No `ToolMessage` exists while paused:** A `ToolMessage` is only created *after* the tool hits its `return` statement. While paused at `interrupt()`, `result["messages"]` contains only `[HumanMessage, AIMessage(tool_calls=...)]` plus `result["__interrupt__"]`.
2. **The paused node/tool re-runs from line 1 on resume:** When `graph.invoke(Command(resume=value), config=config)` runs with the **same `thread_id`**, LangGraph re-enters the paused tool from its top line, and `interrupt(...)` immediately returns `value` instead of pausing again. **Always put real side effects (charging cards, calling refund APIs, sending emails) *after* `interrupt()`, never above it.**

## Historical learner lab record
File: `<PROJECT_ROOT>/support_ticket/27_support_ticket_hitl.py` (aligned with DSwithBappy Video 21 / Chatbot Part 9: Bappy demonstrates `interrupt` in a 1-node chat demo and inside a `purchase_stock` approve/reject tool; our lab applied the exact pattern to `get_order_status` + `issue_refund` and extended it with structured **Edit** support).

### 1. Minimal 1-node pause/resume proof (no LLM)
Proved that `-> ENTERING process_refund node` prints **twice** (once on pause, once on resume), and `AFTER CALL 1` stays `'PENDING'` with `'__interrupt__'`:
```text
-> ENTERING process_refund node
AFTER CALL 1: {'order_id': 'ORD-42', 'amount': 120, 'status': 'PENDING', '__interrupt__': [Interrupt(value='Approve refund of $120 for ORD-42? (yes/no)', id='<INTERRUPT_ID>', response_schema=None)]}
-> ENTERING process_refund node
-> RESUMED with decision: 'yes'
AFTER CALL 2: {'order_id': 'ORD-42', 'amount': 120, 'status': 'REFUND_ISSUED ($120 for ORD-42)'}
```

### 2. Structured Approve / Edit / Reject resumes (no LLM)
Passing a dictionary in `Command(resume=...)` delivered the exact `dict` into `decision`:
```text
=== ticket-approve ===
FINAL STATE: {'order_id': 'ORD-42', 'amount': 120, 'status': 'REFUND_ISSUED ($120 for ORD-42)'}

=== ticket-edit ===
FINAL STATE: {'order_id': 'ORD-42', 'amount': 50, 'status': 'REFUND_ISSUED_EDITED ($50 for ORD-42)'}

=== ticket-reject ===
FINAL STATE: {'order_id': 'ORD-42', 'amount': 120, 'status': 'REFUND_REJECTED'}
```

### 3. Full Groq tool-calling HITL agent (4 paths)
Command:
```bash
uv run 27_support_ticket_hitl.py
```
Observed live receipts (`ChatGroq` + `InMemorySaver` + `get_order_status` + `issue_refund`):
- **`1-safe-status` (`"What is the status of order ORD-42?"`):** `PAUSED: False` | `MESSAGE TYPES: ['HumanMessage', 'AIMessage', 'ToolMessage', 'AIMessage']` | Groq reported `ORD-42` is **in transit**.
- **`2-refund-approve` (`{"action": "approve"}`):** `PAUSED: True` (2 messages before resume, 4 after) | `REFUND_ISSUED: $120 refunded for ORD-42.`
- **`3-refund-edit` (`{"action": "edit", "amount": 50}`):** `PAUSED: True` | Groq reported *"After review, a $50 refund has been issued (the original $120 request was adjusted)."*
- **`4-refund-reject` (`{"action": "reject"}`):** `PAUSED: True` | Groq reported *"a human reviewer has declined the $120 refund request for order ORD-42."*

## Mistakes and fixes
- **Mismatched `StateGraph` schema returning `None`:** passing `StateGraph(RefundState)` while invoking with `{"messages": [HumanMessage(...)]}` caused LangGraph to ignore the undeclared `"messages"` key and return `None`, raising `AttributeError: 'NoneType' object has no attribute 'get'` on `result.get("__interrupt__")`. Switching to `StateGraph(MessagesState)` fixed it immediately. **Rule:** every key passed to `invoke()` or returned by nodes must exist on the schema passed to `StateGraph(...)`.
- **String vs. `dict` resume mismatch:** changing the node to read `decision["action"]` requires updating `Command(resume=...)` from `"yes"` (`str`) to `{"action": "approve"}` (`dict`).

## In production
Use a durable checkpointer (SQLite or PostgreSQL, not `InMemorySaver`) so pending approvals survive server restarts, enforce reviewer authentication/authorization before accepting a `Command(resume=...)`, log who approved/edited/rejected each action for auditing, and guard external side effects with idempotency keys after `interrupt()`.

## Interview questions
::: question Why does `interrupt()` require a checkpointer and a `thread_id`?
`interrupt()` halts execution and returns control to the caller so the server is not blocked while waiting for a human. The checkpointer persists the paused state under `thread_id` so `Command(resume=...)` can reload that exact execution point later.
:::
::: question Why should you never put a payment or email API call *above* `interrupt()` inside the same node or tool?
On resume, LangGraph re-executes the paused node or tool from its first line and returns the resume value from `interrupt()`. Any side effect placed before `interrupt()` would run before approval—and run a second time on resume.
:::
::: question Why was there no `ToolMessage` in `result["messages"]` while `issue_refund` was paused?
A `ToolMessage` is only constructed by `ToolNode` after the tool function finishes and executes its `return` statement. While paused at `interrupt()`, `issue_refund` has not returned yet.
:::

## References
- [LangGraph interrupts and Human-in-the-Loop](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [DSwithBappy Part 9 video](https://www.youtube.com/watch?v=9ZYxMs2pAIA)
- [Course repository](https://github.com/entbappy/Complete-Agentic-AI-Course)
