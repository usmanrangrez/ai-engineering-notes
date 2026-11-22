## What it is and why it matters
Natural-language output is awkward to route on. A validated schema makes fields such as category, sentiment, score, and feedback usable in Python.

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
