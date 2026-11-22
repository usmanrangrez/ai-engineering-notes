## What it is and why it matters
Word counting and character counting both need the reply but do not need each other. They can run as sibling nodes. A combining node must wait for all the results it requires.

## Learn from the beginning
**Prerequisite:** state updates and graph edges. Your goal is to decide which operations are independent, which state each sees, and when a join can safely run.

### Concept 1 — Fan-out schedules independent siblings
**Fan-out** means scheduling more than one branch from a source. **Siblings** are nodes scheduled in the same graph round. Counting words and counting characters can both read the original reply; neither needs the other's new result.

```python
builder.add_edge(START, "count_words")
builder.add_edge(START, "count_characters")
```

The runtime can overlap these nodes. A 0.1-second wait and a 0.2-second wait should overlap; they do not imply a universal speedup for CPU work. Independent external calls also increase instantaneous request pressure. Two branches against the same model do not create a new rate-limit bucket.

### Concept 2 — State updates become visible between rounds
```text
Round 1 input: {reply}
   count_words ------------------> {reply_words}
   count_characters -------------> {reply_chars}
                 boundary: apply both updates
Round 2 input: {reply, reply_words, reply_chars}
   combine_checks
```

A faster sibling cannot publish a newly returned field into another sibling's current input. If count_characters reads reply_words, it gets an older value or a missing-key error. To depend on the new count, move the consumer after count_words with an edge. **Wall-clock completion is not a data dependency.**

### Concept 3 — Merge data and join control separately
A **reducer** combines state updates. `Annotated[list[str], operator.add]` attaches the list-concatenation rule to a state key. When both siblings return check_events, their contributions can be combined instead of conflicting.

```python
check_events: Annotated[list[str], operator.add]
# Each branch returns a delta, not the accumulated history:
return {"check_events": ["words checked"]}
```

Returning `state["check_events"] + [new_event]` would duplicate previous history when the reducer appends it again. Without a reducer, one writer in a later step replaces the old value. Reducers can therefore be useful sequentially too. A reducer does not define when a downstream node runs: that is the edges' job.

An **AND-join** waits for all listed branch endpoints:

```python
builder.add_edge(["count_words", "count_characters"], "combine_checks")
```

Use this explicit relationship when both are required. The list belongs in the first argument; the destination is one node name. With unequal branch depths, joining the true endpoints is especially important. A plain incoming edge can schedule a join while another prerequisite is still being computed in the same round.

## Build it in small pieces
The [offline parallel lab](../examples/08_parallel.py) provides two delayed counters and a join. Start with different output keys. Then add one accumulating events key with its reducer. Finally add a word-limit evaluation after counting words and move the AND-join to that branch's endpoint.

## Check your understanding
Predict whether events will necessarily be stored in completion-time order. Run the lab and compare timestamps with the event list. Store timestamps explicitly if chronology matters.

::: question Exercise receipt: break the merge
Remove the reducer while both siblings still write events. Paste InvalidUpdateError, then restore the reducer and explain why the error happens at write application.
:::
::: question Exercise receipt: repair a dependency
Draw count_words → evaluate_word_limit and the list-source join with count_characters. Show that combine_checks receives word_limit_passed.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/08_parallel.py). Run from the repository root:

```bash
uv run examples/08_parallel.py
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

import operator
from typing import Annotated, NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    reply: str
    words: NotRequired[int]
    chars: NotRequired[int]
    summary: NotRequired[str]
    events: Annotated[list[str], operator.add]

def count_words(state):
    log("count_words START")
    time.sleep(.1)
    words = len(state["reply"].split())
    log(f"count_words DONE words={words}")
    return {"words": words, "events": ["words checked"]}

def count_characters(state):
    log("count_characters START")
    time.sleep(.2)
    chars = len(state["reply"])
    log(f"count_characters DONE chars={chars}")
    return {"chars": chars, "events": ["characters checked"]}

def combine(state):
    log(f"combine START words={state['words']} chars={state['chars']}")
    return {"summary": f"{state['words']} words; {state['chars']} characters"}

builder = StateGraph(State)
for name, action in [("count_words", count_words), ("count_characters", count_characters), ("combine", combine)]:
    builder.add_node(name, action)
builder.add_edge(START, "count_words")
builder.add_edge(START, "count_characters")
builder.add_edge(["count_words", "count_characters"], "combine")
builder.add_edge("combine", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"reply": "Please provide your order ID.", "events": []})
    assert result["words"] == 5 and len(result["events"]) == 2
    log(f"FINAL {result['summary']} events={result['events']}")
```
:::

Author verification output (elapsed times vary):

```text
[  0.22s] count_characters START
[  0.22s] count_words START
[  0.33s] count_words DONE words=5
[  0.43s] count_characters DONE chars=29
[  0.43s] combine START words=5 chars=29
[  0.43s] FINAL 5 words; 29 characters events=['characters checked', 'words checked']
```

| Trace observation | What it establishes |
| --- | --- |
| Both counter START lines precede their DONE lines | The independent branches overlapped. |
| combine START follows both DONE lines | The explicit AND-join waited for both required outputs. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Siblings see the round input. Reducers combine returned deltas; joins coordinate scheduling. With an unequal-depth branch, join evaluate_word_limit and count_characters explicitly. Removing an events reducer makes concurrent writes conflict.
:::

## Historical learner lab record

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
