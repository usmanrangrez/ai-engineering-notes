## What it is and why it matters
Drafting before retrieving policy can produce unsupported promises. A sequential workflow enforces the dependency: the next node runs after its predecessor's update is available.

::: concept Data dependencies dictate edges
Draw an edge `A → B` whenever Node `B` cannot safely compute its output until Node `A` commits its state key (`classify → retrieve_policy → draft_reply`). Notice that putting a key in `state` does **not** automatically send it to the LLM—your drafting node must explicitly format `state["policy"]` into the model prompt.
:::

::: warning Valid graph execution does not prevent upstream classification mistakes
If `classify` mislabels an undelivered parcel as `"refund"` instead of `"delivery"`, every downstream edge runs cleanly while grounding the reply in the **wrong policy**. Separate `issue_category` (what happened) from `requested_action` (what the user asked for).
:::

## Learn from the beginning
**Prerequisite:** state updates and graph construction from chapter 4. Your goal is to know when a fixed ordering is sufficient and when it forces unnecessary work.

### Concept 1 — Sequential means a dependency chain
A reply drafted before policy retrieval can invent refund promises. Putting operations in a chain ensures the later operation receives earlier results. A **sequential workflow** is a fixed series of dependent steps. Each stage uses information already available, then contributes an update.

```text
START --> classify --> retrieve_policy --> draft_reply --> END
```

**Draw A → B when B needs A's completed output.** A sequence is appropriate when every successful input follows the same stages: extract an issue, retrieve the selected policy, draft against that policy. An LLM, a tool, and ordinary Python can all appear in sequential nodes; the shape does not prohibit any of them.

### Concept 2 — Partial updates form a growing record
| Point | State data available |
| --- | --- |
| Input | ticket |
| After classify | ticket, category |
| After retrieve_policy | ticket, category, policy |
| After draft_reply | ticket, category, policy, reply |

`retrieve_policy` must use `state["category"]`, not run classification again. `draft_reply` must receive `state["policy"]`, not rely on the model's memory of company policy. These are explicit data dependencies. A value stored in graph state does not enter the LLM prompt until you actually include it in the model's messages.

### Concept 3 — Correct execution is different from correct content
A graph can execute every edge correctly while producing a wrong answer. If classification selects refund policy for an undelivered parcel, subsequent nodes may faithfully use the wrong policy. This is a data/prompt design problem, not necessarily an edge problem. Log derived values, not just node names, to find where the error first appeared.

The customer's issue and desired action can differ: `issue="delivery"`, `requested_action="refund"`. A larger schema can represent both. Splitting them reduces ambiguity; it does not itself verify whether the customer is entitled to a refund.

## Build it in small pieces
First use deterministic Python classification and a dictionary policy lookup. This makes graph behavior inspectable without model randomness. The [complete sequential lab](../examples/05_sequential.py) provides this version with timestamps. Then replace a single implementation at a time with a model call; preserve the node's input/output keys and the graph edges.

```python
# Inside the drafting node, when adding a real model:
system_instruction = "Draft using only the supplied policy."
human_instruction = f"TICKET: {state['ticket']}\nPOLICY: {state['policy']}"
response = llm.invoke([
    ("system", system_instruction),
    ("human", human_instruction),
])
return {"reply": response.content}
```

This is an integration excerpt: `llm` is a configured chat model, not a global supplied by LangGraph. A complete model setup appears in the start guide. Model text is still untrusted output; a prompt is guidance, not a guaranteed safety constraint.

## When a sequence stops fitting
An unclear ticket should ask for clarification without drafting an invented policy reply. A password issue may use a fixed safety response. A chain forces all stages unless you embed ad hoc branching inside them. A conditional graph makes the branch visible and testable. It extends sequence; it does not make sequential dependencies obsolete.

## Check your understanding
Predict the three node names and which key each writes. Run the offline lab, then compare its trace with the historical LLM trace below.

::: question Exercise receipt: locate the first wrong value
Change the lookup to return an intentionally wrong policy. Paste the policy log and explain why the final wording alone cannot identify the cause.
:::
::: question Exercise receipt: explain the shape
Should two independent quality reviews be added one after another just because the rest is sequential? Draw their data dependencies before answering.
:::


## Runnable example and verified trace

Offline lab (no API key or model call required; [setup guide](../start.html)):

[Open the complete Python file](../examples/05_sequential.py). Run from the repository root:

```bash
uv run examples/05_sequential.py
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

from typing import NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    ticket: str
    category: NotRequired[str]
    policy: NotRequired[str]
    reply: NotRequired[str]

def classify(state):
    log("classify START")
    category = "delivery" if "parcel" in state["ticket"].casefold() else "other"
    log(f"classify DONE category={category!r}")
    return {"category": category}

def retrieve_policy(state):
    log(f"retrieve_policy START category={state['category']!r}")
    policy = {"delivery": "Ask for the order ID.", "other": "Ask for details."}[state["category"]]
    log(f"retrieve_policy DONE policy={policy!r}")
    return {"policy": policy}

def draft_reply(state):
    log(f"draft_reply START policy={state['policy']!r}")
    reply = "Please provide your order ID." if state["category"] == "delivery" else "Please describe the issue."
    log(f"draft_reply DONE reply={reply!r}")
    return {"reply": reply}

builder = StateGraph(State)
for name, action in [("classify", classify), ("retrieve_policy", retrieve_policy), ("draft_reply", draft_reply)]:
    builder.add_node(name, action)
builder.add_edge(START, "classify")
builder.add_edge("classify", "retrieve_policy")
builder.add_edge("retrieve_policy", "draft_reply")
builder.add_edge("draft_reply", END)
graph = builder.compile()

if __name__ == "__main__":
    print(graph.get_graph().draw_mermaid(with_styles=False))
    result = graph.invoke({"ticket": "My parcel is late."})
    log(f"FINAL keys={sorted(result)} reply={result['reply']!r}")
    assert result["policy"] == "Ask for the order ID."
```
:::

Author verification output (elapsed times vary):

```text
graph TD;
	__start__ --> classify;
	classify --> retrieve_policy;
	retrieve_policy --> draft_reply;
	draft_reply --> __end__;

[  0.67s] classify START
[  0.67s] classify DONE category='delivery'
[  0.67s] retrieve_policy START category='delivery'
[  0.67s] retrieve_policy DONE policy='Ask for the order ID.'
[  0.67s] draft_reply START policy='Ask for the order ID.'
[  0.67s] draft_reply DONE reply='Please provide your order ID.'
[  0.67s] FINAL keys=['category', 'policy', 'reply', 'ticket'] reply='Please provide your order ID.'
```

| Trace observation | What it establishes |
| --- | --- |
| classify, retrieve_policy, draft_reply appear in order | Each node ran after its predecessor produced the needed state. |
| FINAL keys include all four fields | Returned updates were merged; they were not standalone replacement dictionaries. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
The chain is classify → retrieve_policy → draft_reply. Each consumes earlier data. Conditional routing can skip unnecessary work; independent reviews can fan out. A correctly followed chain can still use an incorrectly selected policy.
:::

## Historical learner lab record

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
