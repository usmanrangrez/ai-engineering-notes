## What it is and why it matters
The first reply can violate objective requirements or make an unsupported promise. An evaluator produces actionable feedback; an optimizer revises the reply using that feedback.

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
