"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from typing import TypedDict, NotRequired
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    ticket: str
    prepared: NotRequired[bool]
    tracking: NotRequired[str]
    resolution: NotRequired[str]

service = {"available": False}
counts = {"prepare": 0, "tracking": 0, "finish": 0}

def prepare(state):
    counts["prepare"] += 1
    log("prepare START")
    return {"prepared": True}

def tracking(state):
    counts["tracking"] += 1
    log(f"tracking START prepared={state['prepared']}")
    if not service["available"]:
        raise RuntimeError("Simulated tracking outage")
    return {"tracking": "IN_TRANSIT"}

def finish(state):
    counts["finish"] += 1
    log(f"finish START tracking={state['tracking']}")
    return {"resolution": "Ask the courier to investigate."}

builder = StateGraph(State)
for name, action in [("prepare", prepare), ("tracking", tracking), ("finish", finish)]:
    builder.add_node(name, action)
builder.add_edge(START, "prepare")
builder.add_edge("prepare", "tracking")
builder.add_edge("tracking", "finish")
builder.add_edge("finish", END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "recovery-demo"}}

if __name__ == "__main__":
    try:
        graph.invoke({"ticket": "My parcel is late."}, config=config)
    except RuntimeError as error:
        log(f"FAILED {error}")
    saved = graph.get_state(config)
    log(f"SAVED prepared={saved.values['prepared']} next={saved.next}")
    service["available"] = True
    log("RESUME")
    result = graph.invoke(None, config=config)
    assert counts == {"prepare": 1, "tracking": 2, "finish": 1}
    log(f"COUNTS {counts}")
    log(f"FINAL {result['resolution']}")
