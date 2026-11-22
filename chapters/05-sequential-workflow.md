## What it is and why it matters
Drafting before retrieving policy can produce unsupported promises. A sequential workflow enforces the dependency: the next node runs after its predecessor's update is available.

```text
START -> understand_ticket -> retrieve_policy -> draft_reply -> END
```
**Rule:** sequence nodes when later work depends on earlier results. LLMs and tools are both allowed inside this shape.

## Lab: file 08
```bash
uv run 08_support_ticket_sequential.py
```
One early run used an accidental doubled extension, `08_support_ticket_sequential.py.py`; use the actual file name in your checkout.

```text
[  0.00s] ▶ understand_ticket START
[  0.47s] ■ understand_ticket DONE category='delivery' summary='Headphones ordered 12 days ago not arrived; customer wants refund due to delay.'
[  0.47s] ▶ retrieve_policy START category='delivery'
[  0.47s] ■ retrieve_policy DONE policy='For delayed deliveries, ask for the order ID. Check shipment tracking before promising a delivery date or offering a replacement.'
[  0.48s] ▶ draft_reply START
[  0.90s] ■ draft_reply DONE words=29
```
Historical receipt excerpt; spacing normalized for publication. The policy was ready before the writer started.

## Relevant edges
```python
builder.add_edge(START, "understand_ticket")
builder.add_edge("understand_ticket", "retrieve_policy")
builder.add_edge("retrieve_policy", "draft_reply")
builder.add_edge("draft_reply", END)
```
LangGraph schedules the steps, merges updates, and gives subsequent nodes the accumulated state. Handwritten orchestration would need explicit calls, state handling, and instrumentation.

## Mistake: asking for a defect when the parcel never arrived
An earlier classification selected refund and retrieved the defective-product refund policy. The reply then asked about the product's condition. That was a classification/policy-selection problem propagated through a correctly ordered graph.

**Root cause and requested action are different dimensions.** In a larger schema, `issue="delivery"` and `requested_action="refund"` can coexist. A customer requesting a refund does not establish a defect or refund eligibility. Asking for an order ID is appropriate for an existing undelivered order; it is inappropriate if the ticket says no order was placed.

## In production
Use sequential flow for mandatory dependencies. Add routing when some tickets need clarification, account guidance, or escalation instead of the same complete path.

## Interview questions
::: question Why not call the writer first?
It lacks the selected policy. Prompt quality cannot compensate for a missing required dependency.
:::
::: question Does a correct graph guarantee a correct response?
No. The trace can prove execution order while the classifier or retrieved policy is wrong.
:::

## References
- [Graph API and edges](https://docs.langchain.com/oss/python/langgraph/graph-api)
