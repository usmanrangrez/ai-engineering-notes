## What it is and why it matters
“Help me” has no useful policy category. Sending it through policy retrieval anyway creates a confident but irrelevant reply. Routing selects a destination from state.

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
