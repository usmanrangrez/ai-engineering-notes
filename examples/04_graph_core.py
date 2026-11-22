"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from typing import NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    ticket: str
    category: NotRequired[str]

def classify(state: State):
    log(f"classify START ticket={state['ticket']!r}")
    log("classify DONE category='delivery'")
    return {"category": "delivery"}

builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_edge(START, "classify")
builder.add_edge("classify", END)
log("COMPILE (node has not run)")
graph = builder.compile()

if __name__ == "__main__":
    log("INVOKE")
    result = graph.invoke({"ticket": "My parcel is late."})
    log(f"FINAL {result}")
    assert result == {"ticket": "My parcel is late.", "category": "delivery"}
