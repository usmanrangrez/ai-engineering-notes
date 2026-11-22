## What it is and why it matters
Natural-language output is awkward to route on. A validated schema makes fields such as category, sentiment, score, and feedback usable in Python.

## Learn from the beginning
**Prerequisite:** Python dictionaries, classes, and type hints. Your goal is to distinguish a desired response shape from a response whose business claims are true.

### Concept 1 — A schema is a contract
A **schema** describes fields and constraints: a score must be an integer from zero through ten; a category must be one of a known set. An LLM may otherwise answer with free-form prose, missing fields, or an out-of-range score. Pydantic constructs Python objects from input and checks the declared constraints.

```python
from typing import Literal
from pydantic import BaseModel, Field

class Evaluation(BaseModel):
    verdict: Literal["approved", "needs_improvement"]
    score: int = Field(ge=0, le=10)
    feedback: str
```

`BaseModel` supplies validation and serialization methods. `Field(ge=0, le=10)` means greater-than-or-equal to zero and less-than-or-equal to ten. `Literal` narrows a value to the listed constants. A `Literal` annotation alone does not make an ordinary Python function validate inputs; Pydantic or another runtime validator must read it.

### Concept 2 — Validation and serialization have different jobs
```python
result = Evaluation(
    verdict="approved", score=8, feedback="Request the order ID."
)
print(result.score)        # attribute access on a model object
print(result.model_dump())  # a Python dictionary
```

**Validation** checks and may convert input according to the schema. By default, some compatible inputs are coerced; a numeric string can become an integer. **Serialization** converts the object to a transport/storage representation. `model_dump()` returns a Python dictionary; `model_dump_json()` returns JSON text. JSON is a text data format, not another name for every Python dictionary. `ValidationError` reports constraint failures such as `score=99`.

### Concept 3 — Shape does not establish truth
**A valid object can contain a wrong judgment.** A model can return score nine for an unsafe reply and still satisfy this schema. Pydantic establishes the field contract; policy logic, evidence, and evaluation establish other properties.

Our graph state uses `TypedDict`, a description of dictionary keys for type checking and graph channels. Our model-facing response uses `BaseModel`, which validates the response. `NotRequired[int]` in a TypedDict means the key may be absent; it does not mean the value may be `None`.

## Build it in small pieces
First instantiate the schema directly, without a model. Then deliberately set `score=99` and catch `ValidationError`. Only then attach it to a chat model with `llm.with_structured_output(Evaluation, method="function_calling")` for a compatible provider/model. That wrapper requests the shape and parses a response into `Evaluation`; it does not execute arbitrary application code just because the method mentions functions.

`ConfigDict` is Pydantic's configuration dictionary type. For example, `model_config = ConfigDict(extra="forbid")` rejects unexpected fields. A JSON Schema title does not reliably rename the actual tool supplied to a provider. Inspect the tool definition when diagnosing exact tool-name failures.

The [offline contract lab](../examples/02_contracts.py) demonstrates valid data, a forbidden verdict, and an out-of-range score without spending tokens.

## Check your understanding
Predict which fails: an unknown verdict, score eleven, or a polite but factually false feedback string. Verify the first two raise validation errors; explain why the third passes structural validation.

::: question Exercise receipt: separate two contracts
Add a required `reason` field, omit it once, and paste the missing-field error. Does that prove a generated reason is correct?
:::
::: question Exercise receipt: identify the types
Print the types of `result`, `result.model_dump()`, and `result.model_dump_json()`. Paste the three type names.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/02_contracts.py). Run from the repository root:

```bash
uv run examples/02_contracts.py
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

from typing import Literal
from pydantic import BaseModel, Field, ValidationError

class Evaluation(BaseModel):
    verdict: Literal["approved", "needs_improvement"]
    score: int = Field(ge=0, le=10)
    feedback: str

if __name__ == "__main__":
    valid = Evaluation(verdict="approved", score=8, feedback="Request the order ID.")
    log(f"VALID {valid.model_dump()}")
    for changes in ({"score": 99}, {"verdict": "maybe"}):
        try:
            Evaluation(**(valid.model_dump() | changes))
        except ValidationError as error:
            log(f"REJECTED {error.errors()[0]['loc']} {error.errors()[0]['type']}")
        else:
            raise AssertionError("Invalid data was accepted")
```
:::

Author verification output (elapsed times vary):

```text
[  0.08s] VALID {'verdict': 'approved', 'score': 8, 'feedback': 'Request the order ID.'}
[  0.08s] REJECTED ('score',) less_than_equal
[  0.08s] REJECTED ('verdict',) literal_error
```

| Trace observation | What it establishes |
| --- | --- |
| VALID contains score 8 | The object satisfies the declared field constraints. |
| REJECTED lines identify score and verdict | Runtime validation rejected each deliberately invalid input. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Unknown verdicts and out-of-range scores violate declared constraints. A false but well-typed feedback string can pass. The object, model_dump(), and model_dump_json() have model, dict, and str types respectively.
:::

## Historical learner lab record

**Schema:** a description of the fields and constraints expected in data. **Validation:** checking supplied values against that description.

## Contracts versus graph state
Use a `TypedDict` for our graph state and Pydantic v2 models for LLM-facing contracts. A TypedDict describes keys for static checking; it does not perform Pydantic-style runtime validation.

```python
from typing import Literal
from pydantic import BaseModel, Field

class Analysis(BaseModel):
    category: Literal["refund", "delivery", "account", "other"]
    summary: str

class Evaluation(BaseModel):
    score: int = Field(ge=0, le=10)
    feedback: str
```
`Literal` restricts a value to enumerated choices. Pydantic enforces those choices when validating. An ordinary Python type annotation alone does not stop a function from receiving an invalid value.

## Lab evidence
The parallel-review lab used `Evaluation`, a model configured through `with_structured_output`, and `.model_dump()`.
```text
TYPE: Evaluation
{'score': 0, 'feedback': 'Apologize sincerely, acknowledge the frustration, and provide specific, actionable next steps to resolve the issue promptly.'}
```
This is a historical model response; it is not a guaranteed future output.

## Use the result
```python
evaluation = reviewer.with_structured_output(
    Evaluation, method="function_calling"
).invoke("Evaluate this support reply...")
review = {"criterion": "tone", **evaluation.model_dump()}
```
The schema validates numeric bounds. It does not prove the score is wise or the feedback follows policy. A prompt's word limit is not a runtime constraint unless checked separately.

## Mistakes and fixes
| Mistake | Why it fails | Fix |
| --- | --- | --- |
| Expecting Literal to be a dictionary parser | It is a type constraint | Tool invocation handles the argument dictionary |
| Treating valid structured output as factually correct | Structure and meaning are separate | Check policy and domain rules |
| Using a token cap to enforce a sentence limit | Tokens can truncate text mid-sentence | Prompt for brevity and validate the needed property |

## In production
Validate at trust boundaries and keep user-visible constraints explicit. Decide what happens after invalid model output. Provider-native JSON/schema output and tool-based structured output have different support and failure modes.

## Interview questions
::: question Why model_dump() instead of dict()?
These notes use the Pydantic v2 serialization API. model_dump() returns the model's field data as a Python dictionary.
:::
::: question Does a score between 0 and 10 establish answer quality?
No. It establishes a numeric bound. The evaluator and rubric still determine what that score means.
:::

## References
- [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
- [LangChain model structured output](https://docs.langchain.com/oss/python/langchain/models#structured-output)

- [Python Literal and type hints](https://docs.python.org/3.14/library/typing.html#typing.Literal)
