## What it is and why it matters
Terminal START/DONE logs cannot show whether the model received the correct policy. LangSmith records instrumented operations so we can inspect exact input/output payloads, timing, reported usage, and errors.

| Term | Meaning |
| --- | --- |
| Run | One recorded operation, such as a node or model call |
| Trace | Connected runs belonging to one request |
| Thread | Group of traces for one conversation |

Tracing is not conversation storage, does not reveal private model reasoning, and does not make the application production-ready by itself.

## Setup: file 21 and EU destination
```dotenv
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
LANGSMITH_API_KEY=<LANGSMITH_API_KEY>
LANGSMITH_AGENT_ID=<AGENT_ID>
LANGSMITH_AGENT_ENVIRONMENT=local
GROQ_API_KEY=<GROQ_API_KEY>
```
The learner selected an EU LangSmith instance. The dashboard URL and API endpoint identified that region; it was not inferred from personal location. Local is an environment label, not a deployment. Current agent-based workspaces differ from the video's older project-based setup. Do not configure both destinations simultaneously.

## Lab 21A: first trace
```bash
uv run 21_support_ticket_langsmith.py
```
```text
[  0.07s] TRACE AGENT: <AGENT_ID>
[  0.07s] TRACE ENVIRONMENT: local
[  0.07s] ▶ graph START
[  0.11s] ▶ draft_reply START
[  0.59s] ■ draft_reply DONE words=21
[  0.59s] ■ graph DONE
```
Dashboard receipt:
```text
LangGraph                         0.52s
  draft_reply                     0.48s
    openai/gpt-oss-120b            0.40s
Reported tokens: 172
Displayed estimated cost: $0.00004650
```
These durations are nested, not additive. Estimated cost is not a provider billing receipt. The learner opened the model run and confirmed both system and human messages, including the instruction forbidding refunds and delivery promises.

## Why tracing worked without an import in the lesson
The installed dependency chain was langchain-groq -> langchain-core -> langsmith. Framework callback hooks record operation start/end and send trace records through the SDK. A transitive dependency is installed because another package requires it. We later explicitly upgraded it as well.

## Two real setup failures
```text
EnvAddressError: A project ('<LEGACY_PROJECT>') and an address are both set in the environment.
```
Remove LANGSMITH_PROJECT, LANGCHAIN_PROJECT, and LANGCHAIN_SESSION when using the agent-addressing setup. Removing a .env entry does not unset a previously exported shell variable:
```bash
unset LANGSMITH_PROJECT LANGCHAIN_PROJECT LANGCHAIN_SESSION
```
The next error came from older SDKs implicitly adding a project destination:
```text
HTTP 400: Address the run by Agent, or by session_id or session_name, but not both.
Upgrade to langsmith>=0.14.9 and langchain-core>=1.6.11.
```
Historical installed versions were 0.14.8 and 1.6.10. The learner upgraded compatible packages:
```bash
uv add --upgrade langsmith langchain-core
```
Observed working environment: langsmith 0.16.0, langchain-core 1.8.4, langchain-groq 1.2.1. These are lab observations, not a claim they remain latest.

## Lab 21B: naming and metadata
```python
trace_config = {
    "run_name": "support_ticket_reply",
    "tags": ["lesson-21", "delivery"],
    "metadata": {"prompt_version": "v1", "test_case": "late_parcel"},
}
result = graph.invoke(initial_state, config=trace_config)
```
The learner verified the run name, both tags, and both custom metadata fields. Tags/metadata do not change graph state or model instructions. prompt_version is a label maintained by the application, not an automatic prompt-version detector. The root name changes; nested runs keep their own names.

## Lab 21C: grouping traces
Adding metadata thread_id="support-tracing-demo-1" and running twice produced one observed thread with two turns. The first UI view showed no threads; refreshing showed the completed group. No code change was needed.

Metadata thread_id groups LangSmith records. Configurable thread_id with a checkpointer selects graph state. The demo had no checkpointer, so these grouped requests did not remember one another.

## Lab 21D: failed node
```python
if not state["ticket"].strip():
    raise ValueError("Ticket must not be empty.")
```
With ticket="", the node failed before llm.invoke(). The recorded error pointed to draft_reply and the explicit ValueError. Tracing records an exception; it does not automatically fix or retry it.

## Lab 21E: custom Python function
```python
from langsmith import traceable

@traceable(name="count_reply_words")
def count_reply_words(reply: str) -> int:
    return len(reply.split())
```
Call this inside draft_reply after generation. Dashboard evidence:
```text
support_ticket_custom_trace
  draft_reply
    openai/gpt-oss-120b
    count_reply_words
count_reply_words input: generated reply text
count_reply_words output: 18
```
A helper became a traced child run, not another graph node. No edge was added.

## Lab 21F: hide recorded inputs and outputs
```bash
LANGSMITH_HIDE_INPUTS=true LANGSMITH_HIDE_OUTPUTS=true uv run 21_support_ticket_langsmith.py
```
```text
Trace: support_ticket_hidden_payloads
Input: No inputs
Output: No outputs
Metadata: prompt_version=v1, test_case=late_parcel
Model usage: 172 tokens
```
These one-command environment settings affected trace recording, not the prompt sent to Groq, application state, terminal print, old traces, or metadata. They are not a complete redaction policy for names, errors, logs, and attachments.

## In production
Trace selected meaningful work, correlate requests, define retention and payload policy, and avoid treating trace cost estimates as invoices. LangSmith overlaps with application monitoring tools; Sentry and infrastructure monitoring were discussed, not implemented. Model quality still needs evaluation.

## Interview questions
::: question Why can the model reply print while tracing fails?
The model request and telemetry submission are different operations. A clean response does not prove observability records reached their destination.
:::
::: question What is the difference between tracing a run and giving the agent memory?
Tracing records what happened. A checkpointer or application state supplies previous information to future execution.
:::
::: question Why did removing unused imports not fix a model's tool-name error?
It did not. That earlier structured-output response varied across model calls; a successful later call was not evidence of an import-based fix.
:::

## References
- [Trace LangGraph](https://docs.langchain.com/langsmith/trace-with-langgraph)
- [Current setup](https://docs.langchain.com/langsmith/observability-quickstart)
- [Tags and metadata](https://docs.langchain.com/langsmith/trace-with-langchain)
- [Threads](https://docs.langchain.com/langsmith/threads)
- [Custom instrumentation](https://docs.langchain.com/langsmith/annotate-code)
- [Payload controls](https://docs.langchain.com/langsmith/mask-inputs-outputs)
