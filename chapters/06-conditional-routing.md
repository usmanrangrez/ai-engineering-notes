## What it is and why it matters
“Help me” has no useful policy category. Sending it through policy retrieval anyway creates a confident but irrelevant reply. Routing selects a destination from state.

## Learn from the beginning
**Prerequisite:** chapter 5's fixed chain. Your goal is to trace a decision from saved state to a selected destination and identify the nodes that must be skipped.

### Concept 1 — A router chooses the next path
A **router** is a function that examines current state and returns a decision. It should normally be quick, deterministic, and free of side effects. A classification node may call a model to obtain `category`; the router then applies Python rules to that saved category. The router is not required to ask the LLM again.

```python
from typing import Literal

def route(state: State) -> Literal["clarify", "account", "policy"]:
    category = state["category"]
    if category == "other":
        return "clarify"
    if category == "account":
        return "account"
    return "policy"
```

This is `if / elif / else` represented as graph control flow. In this lesson the router returns one label, so one destination is selected. Other graph patterns can intentionally return multiple destinations; do not confuse those with this single-choice route.

### Concept 2 — A route label can differ from a node name
```python
builder.add_conditional_edges(
    "understand_ticket", route,
    {"clarify": "ask_clarification", "account": "account_help", "policy": "retrieve_policy"},
)
```

The **path map** translates a decision label into a registered destination name. `"policy"` describes the decision; `"retrieve_policy"` names the node. If you return node names directly, a map may be unnecessary. A router returning a label absent from the map is a wiring error, not a classification-quality issue.

**Conditional edges choose; ordinary edges always schedule their destination when their source completes.** Do not also add an ordinary edge from `understand_ticket` to `retrieve_policy` if that work should be skipped on the clarification path. That edge is not canceled by the router.

### Concept 3 — Nested means another decision after more information
```text
understand_ticket
    | other --> ask_clarification --> END
    | account --> account_help ----> END
    | negative --> diagnose_issue
    |                 | high urgency --> prepare_escalation --> END
    |                 | low urgency ---> retrieve_policy --> draft --> END
    | ordinary -----------------------> retrieve_policy
```

The first decision uses category/sentiment. The diagnosis branch creates new state such as urgency. A second router can now use urgency. That second, later decision is the **nested decision**; it need not be visually indented Python inside the first router. Node names such as `diagnose_issue` are application names, not built-in LangGraph operations.

Positive feedback may simply receive thanks. Negative feedback may require diagnosis. Those are business design choices, not universal meanings of positive and negative sentiment. Anger alone should not automatically determine urgency or eligibility in a production application.

## Build it in small pieces
The [offline routing lab](../examples/06_routing.py) first derives a category, then selects clarification/account/policy. Run one case before adding another. This isolates routing from uncertain LLM classification. Once the wiring is correct, swap in structured model classification and inspect both its output and the router's chosen label.

For a route that returns termination directly, annotate `Literal["repair_reply", "__end__"]` and return `END` in the function body. `END` is a runtime constant; use the literal string in the type annotation. Routing to END preserves the current state as a normal completed result.

## Check your understanding
Predict: which node is absent for an account ticket? Run the lab with `"I forgot my password"` and paste the selected path.

::: question Exercise receipt: break the branch
Add an unconditional edge to the policy node alongside the conditional route. Observe unexpected work or conflicting writes; remove the extra edge and explain the mechanism.
:::
::: question Exercise receipt: nested decision
On paper, list the two state fields read by the first and second routers in the diagnosis graph. State which node produces urgency.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/06_routing.py). Run from the repository root:

```bash
uv run examples/06_routing.py
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

import sys
from typing import Literal, NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    ticket: str
    category: NotRequired[str]
    reply: NotRequired[str]

def understand(state):
    text = state["ticket"].casefold()
    category = "account" if "password" in text else "delivery" if "parcel" in text else "other"
    log(f"understand DONE category={category!r}")
    return {"category": category}

def route(state) -> Literal["clarify", "account", "policy"]:
    label = {"other": "clarify", "account": "account", "delivery": "policy"}[state["category"]]
    log(f"ROUTE {label}")
    return label

def ask_clarification(state):
    log("ask_clarification START")
    return {"reply": "What issue do you need help with?"}

def account_help(state):
    log("account_help START")
    return {"reply": "Use the official password-reset page."}

def retrieve_policy(state):
    log("retrieve_policy START")
    return {"reply": "Please provide your order ID."}

builder = StateGraph(State)
builder.add_node("understand_ticket", understand)
for name, action in [("ask_clarification", ask_clarification), ("account_help", account_help), ("retrieve_policy", retrieve_policy)]:
    builder.add_node(name, action)
    builder.add_edge(name, END)
builder.add_edge(START, "understand_ticket")
builder.add_conditional_edges("understand_ticket", route, {"clarify": "ask_clarification", "account": "account_help", "policy": "retrieve_policy"})
graph = builder.compile()

if __name__ == "__main__":
    ticket = sys.argv[1] if len(sys.argv) > 1 else "I forgot my password"
    result = graph.invoke({"ticket": ticket})
    log(f"FINAL {result['reply']}")
```
:::

Author verification output (elapsed times vary):

```text
[  0.22s] understand DONE category='account'
[  0.22s] ROUTE account
[  0.22s] account_help START
[  0.22s] FINAL Use the official password-reset page.
```

| Trace observation | What it establishes |
| --- | --- |
| ROUTE account | The saved category selected the account label. |
| account_help START without retrieve_policy START | Only the mapped account branch ran for this input. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
The account case selects account_help and skips retrieve_policy. Adding an ordinary policy edge schedules extra work despite the router. Nested routing happens when diagnosis produces new information that a second router then reads.
:::

## Historical learner lab record

```text
understand_ticket
  positive feedback -> acknowledge_feedback -> END
  negative ticket   -> diagnose_issue
                         high urgency -> prepare_escalation -> END
                         otherwise    -> category route
  ordinary ticket  -> category route

category route: account -> account_help
                other  -> ask_clarification
                delivery/refund -> retrieve_policy -> draft_reply
```
The second decision is nested in control flow: urgency is evaluated after the negative branch produces diagnosis. It does not require nesting one Python def inside another.

## Route labels and path maps
```python
def route_reply(state: State) -> Literal["repair", "finish"]:
    return "repair" if state["reply_words"] > 25 else "finish"

builder.add_conditional_edges(
    "check_reply", route_reply,
    {"repair": "repair_reply", "finish": END},
)
```
The decision label `repair` need not equal the destination node name `repair_reply`. The router selects; the destination node does work.

## Labs: files 09 and 10
```bash
uv run 09_support_ticket_conditional.py
uv run 10_support_ticket_bounded.py
```
```text
category='other' -> ask_clarification
FINAL REPLY: Could you describe the issue you need help with? For example, is it about a delivery, a return, or access to your account?

category='account' -> account_help
FINAL REPLY: For help accessing your account, use the password-reset option on the official sign-in page. Do not share your password or verification codes.
```
Nested-branch receipt:
```text
[  0.73s] category='delivery' sentiment='negative' -> diagnose_issue
[  0.98s] diagnosis urgency='high'
[  0.98s] category='delivery' urgency='high' -> prepare_escalation
[  0.98s] prepare_escalation DONE status='prepared'
```
The status was prepared, not sent to a real support team. A low-urgency run instead selected retrieve_policy and continued drafting.

## Mistakes and fixes
Return annotations use string literals: `Literal["write", "__end__"]`, not `Literal["write", END]`. The body can still return END. END is a runtime constant, not the literal type expression the annotation needs.

Do not attach an unconditional outgoing edge that schedules work you intended to be exclusive with a conditional route. Inspect draw_mermaid(): dashed connections represent conditional paths. A drawing shows possible paths; the runtime trace proves the path selected in a particular run.

## In production
Branch-specific diagnosis saves calls and avoids applying escalation logic before the needed information exists. Deterministic business checks can route alongside LLM classifications.

## Interview questions
::: question Where is the nested condition in this graph?
The first route decides whether diagnosis is needed. A later route uses the resulting urgency to choose escalation or normal handling.
:::
::: question Is a path-map label a node?
No. It is a decision result mapped to a node or END.
:::

## References
- [Control flow](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [StateGraph reference](https://reference.langchain.com/python/langgraph/graph/state/StateGraph)
