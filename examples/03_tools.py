"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from typing import Literal
from langchain_core.tools import tool
from pydantic import ValidationError

@tool
def lookup_policy(category: Literal["refund", "delivery"]) -> str:
    """Look up a policy for a known support category."""
    return {"refund": "Verify the order.", "delivery": "Ask for the order ID."}[category]

if __name__ == "__main__":
    log(f"TOOL {lookup_policy.name} ARGS {lookup_policy.args}")
    result = lookup_policy.invoke({"category": "delivery"})
    log(f"POLICY {result}")
    assert result == "Ask for the order ID."
    try:
        lookup_policy.invoke({"category": "billing"})
    except ValidationError as error:
        log(f"REJECTED {error.errors()[0]['type']}")
    else:
        raise AssertionError("Unknown category was accepted")
