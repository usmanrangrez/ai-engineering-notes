## What it is and why it matters
An agent waits on model APIs, search services, tools, and databases. Async Python lets one execution context do other work while an awaited I/O operation is waiting. It does not automatically make CPU work faster.

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
