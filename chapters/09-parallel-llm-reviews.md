## What it is and why it matters
A polite reply can still approve an unauthorized refund. Independent tone and policy reviews expose different defects. An average score can hide a critical failure.

::: warning Never hide a mandatory policy gate inside an average score
In our live lab, a reply scored **Tone = 9/10** and **Policy = 0/10** (because it falsely promised an unauthorized refund). A naive mean hides critical violations behind polite wording—always enforce **hard boolean gates** for policy/safety criteria, and use averages only as secondary quality telemetry.
:::

::: tip Always tag parallel review items with their `criterion`
Parallel branches finish in non-deterministic wall-clock order. Include `{"criterion": "policy", ...}` inside every reducer-merged review dict so downstream aggregation never relies on fragile list positions (`reviews[0]` vs. `reviews[1]`).
:::

## Learn from the beginning
**Prerequisite:** reducers, siblings, and Pydantic contracts. Your goal is to distinguish successful aggregation from a trustworthy approval decision.

### Concept 1 — Independent criteria can examine the same candidate
An **evaluator** measures a candidate against a criterion. A tone evaluator asks whether a reply is respectful; a policy evaluator asks whether its claims follow company rules. They can both read the same candidate and run concurrently. The tone result need not be an input to the policy result.

```text
                 +--> review_tone ----+
reply + policy --+                    +--> combine_reviews --> END
                 +--> review_policy --+
```

Both nodes return an item to a reducer-backed `reviews` list. Give every item a `criterion` so the aggregation does not depend on list position or completion order. A **candidate** is the reply being assessed, not the evaluator's own reply.

### Concept 2 — Structured output uses a transport protocol
`with_structured_output(Evaluation, method="function_calling")` can send an artificial tool/function schema describing the desired response. The model emits arguments for that exact tool name; the provider validates the request and generated call; LangChain parses the arguments into a Pydantic object.

```text
request tools: name="Evaluation", parameters={score, feedback}
model emits:  name="evaluation", arguments={...}
provider:     reject unknown name --> HTTP 400
```

Names are case-sensitive. This was the actual category of failure in the lab. Removing unused Python imports did not cause the model to respect capitalization; another successful request was a new generation. Sampling, serving changes, or model behavior can make the malformed output intermittent. Without the actual request/response, do not claim an exact underlying model defect has been proven.

**Function calling is an interface, not a guarantee that every model always follows it.** It remains useful for machine-readable requests and external operations. JSON mode primarily changes output format; it does not execute tools. Schema-constrained JSON is a separate capability whose support depends on provider and model. Validate the complete integration before choosing a mode.

### Concept 3 — Averages can hide hard failures
Tone nine plus policy zero averages to 4.5. A future tone ten plus policy six could pass a naive average threshold while the policy evaluator still identifies a serious violation. Use a required policy gate if policy is mandatory; report the average as descriptive information, not as permission to act.

A **judge model** can also give bad advice. Our tone judge recommended confirming refund details that the policy prohibited. Separate the judge's task, ground it in relevant constraints, and never let an unchecked summary become authorization. A second LLM summarizing feedback can repeat the first judge's mistake.

## Build it in small pieces
First run one evaluator and inspect its return type. Then wrap it as a graph node returning `{"reviews": [review]}`. Add the second evaluator. Only after both work, wire the AND-join and compute the mean in Python. Arithmetic does not need a third LLM call. Add prose summarization only if its value justifies latency and another failure point.

This chapter's real model outputs appear below. The earlier reviewer model ID is a historical observation; its catalog entry is currently marked preview, so it is not our production-model recommendation. New readers should use a currently supported model and verify tool/structured-output support in the provider's documentation. Keep model prompts in separate system_instruction and human_instruction variables so inspection is straightforward.

## Check your understanding
Predict whether a polite reply that falsely promises delivery can receive high tone and low policy scores. Compare the historical receipt below and explain why the scores need not agree.

::: question Exercise receipt: keep the policy gate visible
Given tone=10 and policy=0, print the average and a separate `policy_passed=False`. Explain which value should govern sending the reply.
:::
::: question Exercise receipt: locate the failure layer
For an unknown tool-name HTTP 400, identify whether the node returned a bad reducer update or whether the provider rejected the response before that node could return.
:::


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Tone and policy measure different properties, so high tone and low policy can coexist. An average is not a substitute for a mandatory policy gate. The unknown-tool error occurred before the graph node could return its reviews update.
:::

## Historical learner lab record

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
The reviewer model identifier in the original lab was qwen/qwen3.8-27b. It worked in those observed runs, but Groq’s model catalog checked on 2026-11-22 lists it as a preview model. The historical client options and current schema/tool behavior still need integration testing before reuse. Later lessons use the learner's working Groq model openai/gpt-oss-120b. Do not copy a historical model ID as a promise of availability.

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

- [Groq model support](https://console.groq.com/docs/models)
