## What it is and why it matters
A successful graph trace does not establish a good answer. Evaluation compares an application's output with specified criteria on known cases.

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
