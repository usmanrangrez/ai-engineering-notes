## What it is and why it matters
A successful graph trace does not establish a good answer. Evaluation compares an application's output with specified criteria on known cases.

::: concept The 4 pillars of Systematic Evaluation
1. **Dataset:** curated input cases + reference expectations (including tricky/adversarial edge cases).
2. **Target:** the versioned graph or prompt being tested.
3. **Evaluator:** deterministic Python check or LLM-judge rubric scoring each output.
4. **Experiment:** running a target across the full dataset to catch **regressions** before shipping a prompt or model change.
:::

::: warning Beware False Positives and False Negatives
A phrase-presence check (`"order id" in reply.lower()`) passes `"Please provide your order ID. Your refund is approved."` (**false positive** — unsafe reply passes!) and fails `"Please share your purchase number"` (**false negative** — good paraphrase fails!). Always name metrics honestly after what they actually measure.
:::

## Learn from the beginning
**Prerequisite:** inspecting traces and ordinary Python checks. Your goal is to say exactly what a metric measures and what evidence would be needed before claiming an improvement.

### Concept 1 — A dataset fixes the cases being tested
A **dataset** is a collection of examples. An example includes input and may include reference requirements. A **reference** is the expected answer or criterion used for comparison; it is not the generated output. A **target** is the application/function being tested.

```text
input ticket --> target graph --> generated reply
reference requirements --------> evaluator --> score + explanation
```

For support, a reference might require an order-ID request and a word limit rather than one exact ideal sentence. Natural-language tasks often have many acceptable answers. Exact string equality is appropriate only when exact text is the real requirement.

### Concept 2 — An evaluator operationalizes a claim
An **evaluator** implements a measurement. If the code checks phrase presence and word count, its result answers those two questions. Calling it basic_requirements is reasonable; calling it perfectly_policy_safe would claim far more than it measures.

```python
contains_phrase = "order id" in reply.casefold()
within_limit = len(reply.split()) <= 30
passed = contains_phrase and within_limit
```

`casefold` normalizes case for matching. `split()` counts whitespace-separated pieces in this definition of a word; it is not a universal linguistic word counter. This check can accept “Do not send your order ID” because the phrase exists. It can also accept an unauthorized refund claim added to a short reply. These are **false positives**: the metric passes an output that violates the broader intended requirement.

A **false negative** rejects something acceptable, such as a correct request phrased “Please share your purchase identifier” if the exact phrase order ID was mandatory only in our evaluator, not the real policy. Both errors reveal a mismatch between the intended property and the implemented measurement.

### Concept 3 — An experiment compares versions on cases
An **experiment** records a target version's outputs and evaluation results across examples. A **regression** is a previously acceptable behavior that worsens after a change. Reuse representative cases when changing prompts, models, or routing so differences can be assessed rather than remembered vaguely.

The learner completed dataset creation and a local evaluator check. A full recorded LangSmith experiment has not been run in this course checkpoint. These notes teach its meaning without claiming that pending lab is done. Do not silently switch from a local unit check to a hosted experiment with API cost and data upload.

## Build it in small pieces
Start by calling the evaluator on two handcrafted output dictionaries, one expected to pass and one expected to fail. This tests the evaluator before testing an uncertain model. Next add an adversarial case designed to exploit the metric's blind spot. **Adversarial** here means deliberately chosen to expose a weakness, not necessarily an attacker in production.

The [offline evaluator lab](../examples/20_evaluator.py) prints those three cases without a service call. The passing-but-unsafe case is valuable: it demonstrates why a Boolean receipt must be interpreted against the implemented checks. It does not add an LLM judge to hide the weakness.

Later, choose policy checks, judge rubrics, or human review for the properties simple code cannot cover. A **rubric** defines criteria and scoring guidance. Judge models need validation too; their scores are not objective truth merely because they are numeric. Keep a development set for iteration and held-out cases for less biased assessment when the project grows.

## Check your understanding
Predict whether “Please provide your order ID. Your refund is approved.” passes the phrase/length check. Run it, then explain why a green result would not authorize sending it.

::: question Exercise receipt: reveal a blind spot
Write one passing unsafe reply and one acceptable paraphrase that fails. Paste both Boolean scores and name the unmeasured business property.
:::
::: question Exercise receipt: distinguish two workflows
Describe what tracing one production request tells you and what running the same dataset across two prompt versions tells you. They are complementary evidence, not interchangeable tests.
:::


## Runnable example and verified trace

Offline lab (no API key or model call required; [setup guide](../start.html)):

[Open the complete Python file](../examples/20_evaluator.py). Run from the repository root:

```bash
uv run examples/20_evaluator.py
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

def evaluate(reply):
    contains_phrase = "order id" in reply.casefold()
    within_limit = len(reply.split()) <= 30
    return {"score": contains_phrase and within_limit, "contains_phrase": contains_phrase, "words": len(reply.split())}

if __name__ == "__main__":
    cases = {
        "valid": "Please provide your order ID so support can check tracking.",
        "invalid": "Your parcel will arrive tomorrow.",
        "unsafe_but_metric_passes": "Please provide your order ID. Your refund is approved.",
    }
    for name, reply in cases.items():
        log(f"{name} {evaluate(reply)}")
    assert evaluate(cases["valid"])["score"] is True
    assert evaluate(cases["invalid"])["score"] is False
    assert evaluate(cases["unsafe_but_metric_passes"])["score"] is True
    log("A PASS MEASURES THE CHECKS, NOT COMPLETE SAFETY")
```
:::

Author verification output (elapsed times vary):

```text
[  0.00s] valid {'score': True, 'contains_phrase': True, 'words': 10}
[  0.00s] invalid {'score': False, 'contains_phrase': False, 'words': 5}
[  0.00s] unsafe_but_metric_passes {'score': True, 'contains_phrase': True, 'words': 9}
[  0.00s] A PASS MEASURES THE CHECKS, NOT COMPLETE SAFETY
```

| Trace observation | What it establishes |
| --- | --- |
| unsafe_but_metric_passes has score=True | The evaluator measured phrase/length, not complete policy compliance. |
| invalid has score=False | The missing phrase caused this specific failure. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
A short unsafe reply can pass phrase/word-count tests. An acceptable paraphrase can fail a narrow lexical condition. The metric must be named and interpreted against its actual checks. Dataset experiments and single-request traces answer different questions.
:::

## Historical learner lab record

```text
Dataset inputs -> target application -> actual outputs
                                          |
Dataset references ----------------------> evaluator -> scores
```
**Dataset:** collection of example inputs and optional reference data. **Target:** application/function under test. **Evaluator:** code or a judge that scores the target's output. **Experiment:** recorded evaluation of a version across examples.

## Scope boundary
Bappy's LangSmith video demonstrated tracing, run names, execution inspection, and thread grouping. It mentioned evaluation but did not implement a full experiment. Dataset and evaluator work was a tutor addition. The learner requested returning to the course progression; full experiments remain planned.

## Lab 22: dataset uploaded
```bash
uv run 22_support_ticket_dataset.py
```
```python
examples = [
    {
        "inputs": {"ticket": "My parcel is five days late."},
        "outputs": {"required_phrase": "order ID", "max_words": 30},
        "metadata": {"case": "ordinary_delay"},
    },
    {
        "inputs": {"ticket": "My parcel is late. Please guarantee it will arrive tomorrow."},
        "outputs": {"required_phrase": "order ID", "max_words": 30},
        "metadata": {"case": "requested_delivery_promise"},
    },
]
```
The learner confirmed both cases appeared in support-ticket-eval-v1. Dataset outputs are our reference requirements, not the model's generated replies. The script reused an existing dataset and avoided a duplicate upload when examples already existed; it was not a general synchronization tool.

## Lab 23: local evaluator
```python
def check_basic_requirements(outputs: dict, reference_outputs: dict) -> dict:
    reply = outputs["reply"]
    phrase = reference_outputs["required_phrase"]
    max_words = reference_outputs["max_words"]
    contains_phrase = phrase.casefold() in reply.casefold()
    word_count = len(reply.split())
    within_limit = word_count <= max_words
    return {
        "key": "basic_requirements",
        "score": contains_phrase and within_limit,
        "comment": f"contains_phrase={contains_phrase}; words={word_count}/{max_words}; within_limit={within_limit}",
    }
```
```bash
uv run 23_support_ticket_evaluation.py
```
```text
VALID: {'key': 'basic_requirements', 'score': True, 'comment': 'contains_phrase=True; words=10/30; within_limit=True'}
INVALID: {'key': 'basic_requirements', 'score': False, 'comment': 'contains_phrase=False; words=5/30; within_limit=True'}
LOCAL EVALUATOR CHECK DONE — no API calls
```

## What that result does not prove
The invalid example failed because it lacked the required phrase. This evaluator did not check the delivery promise. A short reply containing “order ID” and an unauthorized refund approval can still pass. Even phrase presence is not equivalent to asking for the ID correctly; a negated phrase can match too.

**A passing score proves only the implemented criteria.** Mechanical checks, semantic policy checks, human review, and LLM judges cover different properties and can all have limitations.

## In production
Run regression examples before deploying a change, compare prompt/model versions, and turn discovered failures into future test cases. Production tracing and offline evaluation are related but separate workflows. An LLM judge is not required for word counting or schema validity.

## Interview questions
::: question Is this already a complete LangSmith experiment?
No. We uploaded a dataset and ran the scoring function locally. We have not yet executed the target over that dataset and recorded an experiment.
:::
::: question Can a score of 100% mean the application is unsafe?
Yes, if the tests omit important behavior or the evaluator measures a weak proxy.
:::

## References
- [Evaluation overview](https://docs.langchain.com/langsmith/evaluation)
- [Dataset management](https://docs.langchain.com/langsmith/manage-datasets-programmatically)
- [Evaluation workflow](https://docs.langchain.com/langsmith/evaluation-quickstart)

- [LangSmith evaluation concepts](https://docs.langchain.com/langsmith/evaluation)
