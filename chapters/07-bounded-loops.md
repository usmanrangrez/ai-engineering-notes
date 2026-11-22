## What it is and why it matters
A reply can exceed the required word limit. One repair call might still be too long, so send it back to a deterministic checker. Unbounded repetition spends tokens without guaranteeing progress.

```text
draft_reply -> check_reply --valid--> END
                  | too long, budget available
                  v
              repair_reply
                  |
                  +----------> check_reply
```
**Attempt guard:** a state-based business stop. **recursion_limit:** a runtime super-step backstop, not Python call-stack recursion depth and not a count of model retries.

## Lab: file 10
```bash
uv run 10_support_ticket_bounded.py
```
Successful repair receipt:
```text
[  1.11s] check_reply DONE words=35/25 repairs=0/2 too_long=True
[  1.11s] route_reply words=35 repairs=0 -> repair
[  1.11s] repair_reply START attempt=1/2 prompt_hash=df4d5ebe
[  2.17s] repair_reply DONE words=24/25
[  2.17s] check_reply DONE words=24/25 repairs=1/2 too_long=False
[  2.17s] route_reply words=24 repairs=1 -> finish
```
Budget-exit receipt:
```text
check_reply DONE words=46/1 repairs=0/0 too_long=True
route_reply words=46 repairs=0 -> limit_exceeded
FINAL WORD COUNT: 46/1
```
Stopping is not approval. The reply still violated the target after the budget exit.

## Runtime-backstop lab
```python
result = graph.invoke(initial_state, config={"recursion_limit": 1})
```
```text
understand_ticket DONE category='delivery' sentiment='negative'
route_after_understanding -> diagnose_issue
✖ graph STOP: runtime step limit reached
GraphRecursionError: Recursion limit of 1 reached without hitting a stop condition.
```
Only the first processing super-step ran. With no checkpointer, the failed invoke does not return a final result. Earlier teaching shorthand “recursion_limit discards state” was too broad: a checkpointer can preserve committed state for inspection/recovery.

## Prompt invariant
A repair must receive the current reply and actionable violations. Log a hash of the complete repair prompt to check whether relevant input actually changed. A prompt hash is an inspection aid, not proof of improved output.

## In production
Use an attempt cap and runtime backstop as separate safeguards for loops. Return an explicit exit reason. Retry transient provider errors separately from semantic revision; one configured layer should own backoff. SDK max_retries=1 can still allow a retry; it does not mean retries are disabled.

## Interview questions
::: question Can a sequential graph hit recursion_limit?
Yes. It limits graph super-steps, so an excessively small value can stop an acyclic graph too.
:::
::: question What should a budget exit communicate?
The process stopped without necessarily meeting its target. Preserve violations and the exit reason.
:::

## References
- [Graph recursion limit](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT)
- [Checkpointers and recovery](https://docs.langchain.com/oss/python/langgraph/checkpointers)
