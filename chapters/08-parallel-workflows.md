## What it is and why it matters
Word counting and character counting both need the reply but do not need each other. They can run as sibling nodes. A combining node must wait for all the results it requires.

```text
START --+--> count_words ------> evaluate_word_limit --+
        |                                              +--> combine_checks -> END
        +--> count_characters ------------------------+
```
**Barrier:** the boundary where a graph execution round completes and its updates become available to the next round.

## Lab: file 11
```bash
uv run 11_support_ticket_parallel.py
```
```text
[  0.00s] ▶ count_characters START
[  0.00s] ▶ count_words START
[  1.01s] ■ count_words DONE words=24
[  4.01s] ■ count_characters DONE characters=133
[  4.01s] ▶ combine_checks START words=24 characters=133
```
Elapsed time was governed by the slow sibling, rather than adding one second and four seconds. Coarse identical timestamps alone are not a universal proof of simultaneity; the graph scheduling and overlapping intervals establish this lab's concurrency.

## Can a sibling read the new word count?
No. Siblings in the same super-step see the state from before that round. A faster count_words does not make its newly returned reply_words visible inside a still-running count_characters. An already-existing reply_words would be an older value. Add a dependency if the result is needed.

## Reducer error and fix
```text
InvalidUpdateError: At key 'check_events': Can receive only one value per step. Use an Annotated key to handle multiple values.
```
```python
check_events: Annotated[list[str], operator.add]
# Each node returns only its new contribution:
return {"check_events": ["count_words completed"]}
```
A reducer combines updates. Concurrent writes require a compatible combination strategy. Reducers are also useful for accumulation across sequential steps; “if and only if concurrent” was an incorrect earlier simplification. Without an accumulating reducer, a later list replaces the prior list.

## Unequal branch depths
```python
builder.add_edge(START, "count_words")
builder.add_edge(START, "count_characters")
builder.add_edge("count_words", "evaluate_word_limit")
builder.add_edge(["evaluate_word_limit", "count_characters"], "combine_checks")
```
The list in the first position is an AND-join. Separate incoming edges are not a reliable substitute for an explicit all-sources join across unequal depths. In the faulty shape, combine_checks could run in the same round as evaluate_word_limit and lack word_limit_passed; it is not simply “the one-second branch outran the four-second branch.”

The destination of add_edge is one string. Fan-out uses separate edges; `add_edge("x", ["a", "b"])` is invalid.

## In production
Keep genuinely independent reviews concurrent, cap request pressure, and combine only after required branch endpoints complete. Accumulated list order is not a trustworthy chronological event log; our output listed character completion before word completion despite the reverse finishing times.

## Interview questions
::: question What does add_edge([a, b], join) mean?
Wait for both named sources before scheduling join.
:::
::: question Why didn't the four-second sleep cause the missing-state bug by itself?
Updates become visible at super-step boundaries. The graph's dependency shape, not just wall-clock speed, determined what state the consumer saw.
:::

## References
- [Graph API: super-steps, reducers and edges](https://docs.langchain.com/oss/python/langgraph/graph-api)
