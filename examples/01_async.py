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
