## What it is and why it matters
A polite reply can still approve an unauthorized refund. Independent tone and policy reviews expose different defects. An average score can hide a critical failure.

```text
START -> review_tone ---+
                       +-> combine_reviews -> END
START -> review_policy -+
```
Each reviewer returns a one-item list into a shared accumulating reviews field. The join waits for both.

## Lab: file 12
```bash
uv run 12_support_ticket_parallel_llm.py
```
```text
[  0.00s] ▶ review_policy START
[  0.00s] ▶ review_tone START
[  0.53s] ■ review_policy DONE score=0/10
[  0.83s] ■ review_tone DONE score=9/10
[  0.83s] ▶ combine_reviews START
[  1.25s] ■ combine_reviews DONE reviews=2 average=4.50/10
```
The writer's sample falsely approved a refund and promised tomorrow's delivery. A high tone score did not make that acceptable. The LLM summary even repeated unsafe advice to confirm refund details, demonstrating that a summarizer is another fallible model call.

## Code shape
```python
reviews: Annotated[list[dict], operator.add]

builder.add_edge(START, "review_tone")
builder.add_edge(START, "review_policy")
builder.add_edge(["review_tone", "review_policy"], "combine_reviews")
builder.add_edge("combine_reviews", END)
```
An average is descriptive. A business rule can require policy compliance independently of that average.

## The Evaluation versus evaluation failure
```text
groq.BadRequestError: Error code: 400
tool call validation failed: attempted to call tool 'evaluation' which was not in request.tools
```
with_structured_output(Evaluation, method="function_calling") supplied a schema tool name. On a failed run the model generated a different-case function name. Tool names must match the supplied schema; an otherwise sensible score was insufficient.

Removing unused imports did not cause the next run to succeed. Generation is variable, and the next response happened to conform. Configuring a schema title can align a name, but it is not a guarantee the model will obey. Verify provider/model support before choosing tool-based versus native JSON-schema output.

## Historical model caveat
The reviewer model identifier in the original lab was qwen/qwen3.8-27b. It worked in those observed runs, but its current catalog availability has not been independently verified here. Later lessons use the learner's working Groq model openai/gpt-oss-120b. Do not copy a historical model ID as a promise of availability.

## In production
Enforce hard policy gates, keep feedback actionable, and handle malformed structured output explicitly. Parallel calls increase instantaneous model-scoped token pressure. Repeating a malformed request blindly is not the same as handling a transient service outage.

## Interview questions
::: question Why isn't average_score a sufficient approval rule?
A critical policy failure can be offset numerically by a strong score on a less critical criterion.
:::
::: question Is structured output necessarily a real business tool call?
No. The tool-calling mechanism can be used only to obtain schema-shaped data. Application code need not execute an external action.
:::

## References
- [Model structured output](https://docs.langchain.com/oss/python/langchain/models#structured-output)
- [Groq model documentation](https://console.groq.com/docs/models)
