## What it is and why it matters
The first reply can violate objective requirements or make an unsupported promise. An evaluator produces actionable feedback; an optimizer revises the reply using that feedback.

## Learn from the beginning
**Prerequisite:** bounded loops and evaluation schemas. Your goal is to explain what actually changes between attempts and why stopping does not always mean convergence.

### Concept 1 — Evaluation supplies direction for revision
An **evaluator–optimizer workflow** measures a candidate, produces feedback, revises the candidate, and measures again. The optimizer here is a revising model, not necessarily a numerical optimization algorithm.

```text
candidate --> check mechanical rules --> evaluate meaning --> route
   ^                                                       | approved --> END
   |                                                       | budget/plateau --> END
   +---------------- revise using current feedback <-------+
```

A generic “try again” prompt does not tell the model what was wrong. Provide the current candidate, original task/policy, measured violations, and actionable feedback. Replacing the reply in state matters: evaluating the initial reply repeatedly creates the appearance of a loop without progress.

### Concept 2 — Hybrid evaluation assigns work to the right mechanism
**Deterministic** means the same input produces the same output under the same rules. Python can count words or detect an exact phrase cheaply. **Semantic evaluation** considers meaning: “refund has been authorized” means much the same as “refund is approved” even though the strings differ.

Our exact-match rule missed a paraphrased refund approval. A model evaluator identified it. That does not make model judgment infallible; it shows complementary coverage. Rule score four out of four meant four implemented string/count checks passed, not that all possible company policies were satisfied.

```python
human_instruction = (
    f"POLICY:\n{state['policy']}\n\n"
    f"CURRENT REPLY:\n{state['reply']}\n\n"
    f"RULE VIOLATIONS:\n{state['violations']}\n\n"
    f"REVIEW FEEDBACK:\n{state['evaluation']['feedback']}"
)
```

This is a prompt-building excerpt, not a complete node. Adjacent strings in parentheses concatenate; commas would make a tuple. The real Groq 400 about messages.1.content came from sending the wrong content shape, not a graph-edge issue.

### Concept 3 — History makes progress inspectable
A **trajectory** is the sequence of candidates and evaluations. Record revision number, candidate text, rule violations, semantic score, and verdict together. A scalar score can show improvement; a binary verdict cannot show whether quality is improving while still unacceptable.

A **plateau** means the chosen progress measure stopped improving over a defined window. For example, two consecutive non-positive score changes might trigger an exit. Define the window and threshold before implementing it; two observations [1, 4] are improvement, not a plateau. Scores from an LLM can be noisy, so a numerical stopping rule is a heuristic, not proof that no better candidate exists.

**Approval, plateau, and budget exhaustion are different outcomes.** Test all three. When a maximum-score candidate passes immediately, zero revisions is correct; for teaching the loop, choose a known failing initial candidate rather than changing the target secretly.

## Build it in small pieces
Start with the deterministic loop from chapter 7. Add history of checks. Then introduce one semantic evaluator between the rule node and router. Finally make the reviser consume both kinds of feedback. Do not add unused evaluator nodes that are never registered or reachable. Inspect the Mermaid diagram and actual node START logs to establish what ran.

The [offline refinement lab](../examples/10_iterative.py) demonstrates feedback, candidate replacement, history, and a bounded exit with deterministic revisions. It teaches the state mechanism. It does not simulate having proven an LLM judge's accuracy.

## Check your understanding
Predict whether identical prompt hashes on successive attempts prove learning. They prove identical prompt bytes; the loop may be spending tokens without incorporating new evidence.

::: question Exercise receipt: demonstrate an inert loop
In the offline lab, make revise return the same candidate. Paste the repeated score and budget exit. Restore the useful revision afterwards.
:::
::: question Exercise receipt: demonstrate the blind spot
Run the exact-phrase checker on “refund has been authorized.” Report the score and explain why a passing lexical test is insufficient.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/10_iterative.py). Run from the repository root:

```bash
uv run examples/10_iterative.py
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

import operator
from hashlib import sha256
from typing import Annotated, Literal, TypedDict, NotRequired
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    reply: str
    revisions: int
    max_revisions: int
    violations: NotRequired[list[str]]
    history: Annotated[list[dict], operator.add]

def check(state):
    text = state["reply"].casefold()
    violations = []
    if "order id" not in text:
        violations.append("Ask for the order ID.")
    if "refund is approved" in text:
        violations.append("Remove unauthorized refund approval.")
    score = 2 - len(violations)
    log(f"check revision={state['revisions']} score={score}/2 violations={violations}")
    return {"violations": violations, "history": [{"revision": state["revisions"], "reply": state["reply"], "score": score}]}

def route(state) -> Literal["finish", "revise"]:
    if not state["violations"] or state["revisions"] >= state["max_revisions"]:
        log(f"STOP reason={'approved' if not state['violations'] else 'budget'}")
        return "finish"
    return "revise"

def revise(state):
    prompt = f"CURRENT: {state['reply']} FEEDBACK: {state['violations']}"
    log(f"revise START prompt_hash={sha256(prompt.encode()).hexdigest()[:8]}")
    # A deterministic stand-in proves state flow, not LLM quality.
    reply = "Please provide your order ID so support can check tracking."
    log("revise DONE")
    return {"reply": reply, "revisions": state["revisions"] + 1}

builder = StateGraph(State)
builder.add_node("check", check)
builder.add_node("revise", revise)
builder.add_edge(START, "check")
builder.add_conditional_edges("check", route, {"finish": END, "revise": "revise"})
builder.add_edge("revise", "check")
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"reply": "Your refund is approved.", "revisions": 0, "max_revisions": 2, "history": []}, config={"recursion_limit": 20})
    assert [row["score"] for row in result["history"]] == [0, 2]
    log(f"HISTORY {result['history']}")
```
:::

Author verification output (elapsed times vary):

```text
[  0.22s] check revision=0 score=0/2 violations=['Ask for the order ID.', 'Remove unauthorized refund approval.']
[  0.22s] revise START prompt_hash=ec5a000f
[  0.22s] revise DONE
[  0.22s] check revision=1 score=2/2 violations=[]
[  0.22s] STOP reason=approved
[  0.22s] HISTORY [{'revision': 0, 'reply': 'Your refund is approved.', 'score': 0}, {'revision': 1, 'reply': 'Please provide your order ID so support can check tracking.', 'score': 2}]
```

| Trace observation | What it establishes |
| --- | --- |
| Scores change from 0/2 to 2/2 | The revision replaced the candidate and the next check measured it. |
| HISTORY contains two candidate records | The reducer accumulated evaluation history instead of keeping only the last record. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Changing the candidate and incorporating feedback makes the loop meaningful. An unchanged candidate can consume the whole budget. Exact phrase rules miss paraphrases; semantic evaluators can help but are fallible. Scores [1,4] show improvement, not plateau.
:::

## Historical learner lab record

```text
check_rules -> evaluate_reply -> route
                                approved -> END
                                budget / plateau -> END with reason
                                revise -> revise_reply -> check_rules
```
A bounded loop repeats work; evaluator–optimizer specifically uses the evaluation to improve the next candidate.

## Labs: file 13 stages
```bash
uv run 13_support_ticket_iterative.py
```
Deterministic-stage receipt:
```text
check_rules DONE score=1/4 violations=['Ask for the order ID.', "Remove the claim 'refund is approved'.", "Remove the promise 'arrive tomorrow'."]
revise_reply START revision=1/4 prompt_hash=cdefbec4
revise_reply DONE words=19
check_rules DONE score=4/4 violations=[]
route_after_rules scores=[1, 4] revisions=1/4 -> finish
```
The changed reply and reevaluation prove the feedback loop, even though this case needed only one revision.

## Lexical checks can miss meaning
```text
Reply: Please provide your order ID. Your refund has been authorized; expect the parcel tomorrow.
PYTHON CHECK: rule_score=4, violations=[]
LLM CHECK: verdict='needs_improvement' score=2/10
Feedback: Remove refund authorization and delivery promise; only request order ID for tracking.
```
The Python rules checked specific strings and missed paraphrases. The judge caught the semantic violation. This is why the system became hybrid: deterministic checks for exact properties, model judgment for meaning, with neither treated as infallible.

Final hybrid receipt:
```text
route_after_evaluation quality_scores=[2] revisions=0/4 -> revise
revise_reply START revision=1/4 prompt_hash=8fd15cb7
revise_reply DONE words=15
check_rules DONE score=4/4 violations=[]
evaluate_reply DONE verdict='approved' score=9/10
route_after_evaluation quality_scores=[2, 9] revisions=1/4 -> finish
FINAL REPLY: Please provide your order ID so we can check the tracking details for your shipment.
```

## Track improvement rather than only verdicts
Store revision number, reply, violations, score, and feedback in history. A plateau check needs a defined window and minimum improvement threshold. A rising [1, 4] trajectory is not a plateau; the earlier printed PLATEAU CHECK: True was inconsistent with the intended mechanism, not proof the detector worked correctly.

The revision prompt must include the latest reply and feedback. A hash helps inspect changing inputs. A changed hash alone does not establish improvement.

## Message-format failure
A malformed human message payload caused Groq to reject messages.1.content: it must be a string or supported content blocks, not an arbitrary dictionary. Put formatted human instructions in a string variable before passing ("human", human_instruction).

## In production
Use code for objective criteria, a carefully specified judge for semantic criteria, and a budget/plateau exit. Treat all judge comments as suggestions subject to policy. Re-evaluation belongs after every revision, including the final allowed attempt.

## Interview questions
::: question Why can exact-string rules return a perfect score on a bad answer?
They measure literal matches rather than all semantic equivalents. The metric proves only the implemented checks.
:::
::: question Does changing the prompt guarantee convergence?
No. The target can be contradictory, the optimizer can regress, and judges can be noisy. Preserve the trajectory and stop reason.
:::

## References
- [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [LangSmith evaluation](https://docs.langchain.com/langsmith/evaluation)

- [Workflow patterns](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
