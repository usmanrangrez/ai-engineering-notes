"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from typing import Literal
from pydantic import BaseModel, Field, ValidationError

class Evaluation(BaseModel):
    verdict: Literal["approved", "needs_improvement"]
    score: int = Field(ge=0, le=10)
    feedback: str

if __name__ == "__main__":
    valid = Evaluation(verdict="approved", score=8, feedback="Request the order ID.")
    log(f"VALID {valid.model_dump()}")
    for changes in ({"score": 99}, {"verdict": "maybe"}):
        try:
            Evaluation(**(valid.model_dump() | changes))
        except ValidationError as error:
            log(f"REJECTED {error.errors()[0]['loc']} {error.errors()[0]['type']}")
        else:
            raise AssertionError("Invalid data was accepted")
