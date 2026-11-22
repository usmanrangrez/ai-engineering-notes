## What it is and why it matters
An agent waits on model APIs, search services, tools, and databases. Async Python lets one execution context do other work while an awaited I/O operation is waiting. It does not automatically make CPU work faster.

## Learn from the beginning
**Prerequisite:** ordinary Python functions and function calls. No AI library is needed here. Your goal is to explain why two network requests can overlap without pretending that Python runs every instruction simultaneously.

### Concept 1 — Waiting is different from computing
An LLM request spends much of its time waiting for another machine. **I/O** means input/output: network traffic, disk access, or a database response. During that wait, another independent request could make progress. A synchronous call keeps its calling thread occupied until it returns. An asynchronous operation can suspend and let other scheduled work run.

**Concurrency means overlapping progress; parallelism means simultaneous execution.** Async is especially useful for waiting on I/O. It does not automatically make a CPU-heavy calculation faster.

### Concept 2 — A coroutine must actually be run
A **coroutine** is a suspendable computation created by calling an `async def` function. Calling it makes a coroutine object; it does not give you its completed result. `await` waits for its result while permitting cooperative scheduling. An **event loop** manages the runnable and waiting tasks.

```python
async def fetch_policy():
    await asyncio.sleep(1)  # simulated non-blocking I/O
    return "Ask for the order ID."
```

`asyncio.sleep` is a teaching substitute for waiting on a service. Real async network clients provide their own awaitable operations. `time.sleep` inside this function would block the event-loop thread instead.

### Concept 3 — Dependencies determine whether to overlap
```text
Independent: policy request ----+
             profile request ---+--> use both results
Dependent:   read ticket --> classify --> retrieve chosen policy
```

Two consecutive `await` statements are still sequential: the second request starts after the first completes. `asyncio.gather(a(), b())` schedules the awaitables concurrently and returns results in input order. Completion order can differ. A **task** is a scheduled coroutine; you can also schedule explicitly with `create_task`.

## Build it in small pieces
First write an async worker. Give each worker a different delay so the trace exposes overlap. Next call both through `gather`. Finally run the top-level coroutine using `asyncio.run(main())` from a normal script. A notebook that already has an event loop usually uses `await main()` instead of nesting `asyncio.run`.

```python
async def main():
    results = await asyncio.gather(
        worker("policy", 0.1), worker("profile", 0.2)
    )
    print(results)
```

The complete [offline async lab](../examples/01_async.py) defines `worker`, logs its start/end, and includes the imports. Run `uv run examples/01_async.py` from the downloaded repository. It makes no model call.

## Check your understanding
Predict before running: will the total wait be closer to 0.2 or 0.3 seconds? Then compare overlapping START/DONE intervals; scheduler overhead makes exact timings vary.

::: question Exercise receipt: make the work sequential
Replace gather with two consecutive awaits. Paste both START timestamps and the elapsed duration. Explain why the second START moved.
:::
::: question Exercise receipt: identify a dependency
Can drafting a policy-compliant reply start before the required policy has been obtained? Draw the one edge that expresses the dependency.
:::


## Runnable example and verified trace

This is a new, reconstructed offline teaching lab, executed by the notes author on 2026-11-22. It makes no model call and is separate from the historical learner receipts below. [Set up the repository](../start.html) first.

[Open the complete Python file](../examples/01_async.py). Run from the repository root:

```bash
uv run examples/01_async.py
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

import asyncio

async def worker(name, delay):
    log(f"{name} START")
    await asyncio.sleep(delay)
    log(f"{name} DONE")
    return name

async def main():
    results = await asyncio.gather(worker("policy", .1), worker("profile", .2))
    log(f"RESULTS {results}")
    assert results == ["policy", "profile"]

if __name__ == "__main__":
    asyncio.run(main())
```
:::

Author verification output (elapsed times vary):

```text
[  0.03s] policy START
[  0.03s] profile START
[  0.13s] policy DONE
[  0.23s] profile DONE
[  0.23s] RESULTS ['policy', 'profile']
```

| Trace observation | What it establishes |
| --- | --- |
| Both START lines precede the first DONE | The waits overlap; the event loop had both tasks scheduled. |
| RESULTS lists policy before profile | gather returns results in input order, not a sorted completion list. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Two awaited I/O operations scheduled together can overlap. Replacing gather with consecutive awaits delays the second START. A dependent draft must wait for policy; async syntax cannot remove the dependency.
:::

## Historical learner lab record
The following material records the earlier learning checkpoint. New downloadable labs are separately identified as author verification, not historical learner runs.

**Coroutine:** an async function's execution object. Calling an async function creates a coroutine; awaiting it or scheduling it makes it run.

## Mental model
```text
Sequential awaits: A waits -> A finishes -> B waits -> B finishes
Concurrent I/O:    A waits -----------------> finishes
                  B waits --------> finishes
```
`await` pauses the current coroutine at an awaitable operation. `asyncio.gather()` can run multiple awaitables concurrently and collects their results in argument order. `time.sleep()` blocks the calling thread; inside an event-loop coroutine use `await asyncio.sleep()` for a cooperative delay.

## Code to remember
```python
import asyncio

async def check(name: str, delay: float) -> str:
    await asyncio.sleep(delay)
    return name

async def main():
    results = await asyncio.gather(check("policy", 1), check("tracking", 2))
    print(results)

asyncio.run(main())
```
This is a reconstructed refresher, not a recovered learner lab. No timings are claimed for this snippet.

## Lab evidence
The course handoff records async/await, gather, and blocking-call behavior as completed. The original async terminal output was not retained in the supplied conversation. Do not invent a receipt to fill that gap.

## Mistakes and fixes
| Mistake | Mechanism | Fix |
| --- | --- | --- |
| Calling an async function and expecting its result | The call returns a coroutine | Await or schedule it |
| Sequentially awaiting independent requests | The second starts only after the first finishes | Gather genuinely independent operations |
| Calling a blocking SDK in an async node | Blocks the event-loop thread | Use the SDK's async interface or carefully offload blocking I/O |

## In production
Use concurrency limits, cancellation, timeouts, and provider rate limits. Three independent LLM calls can reduce wall-clock time but increase instantaneous token demand. Async alone does not remove those limits.

## Interview questions
::: question Does async mean parallel CPU execution?
No. Async supports cooperative concurrency, especially for I/O. CPU parallelism needs a different execution strategy.
:::
::: question Does gather preserve completion order?
Its result list follows input order, not the order requests finish.
:::

## References
- [Python coroutines and tasks](https://docs.python.org/3.14/library/asyncio-task.html)

- [Python asyncio tasks](https://docs.python.org/3.14/library/asyncio-task.html)
