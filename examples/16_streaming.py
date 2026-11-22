"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from typing import TypedDict, NotRequired
from langgraph.graph import START, END, StateGraph
from langgraph.config import get_stream_writer
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    ticket: str
    category: NotRequired[str]
    reply: NotRequired[str]

def classify(state):
    log("classify START")
    return {"category": "delivery"}

def prepare(state):
    log("prepare START")
    writer = get_stream_writer()
    writer({"stage": "drafting"})
    time.sleep(.05)
    writer({"stage": "completed"})
    return {"reply": "Please provide your order ID."}

builder = StateGraph(State)
builder.add_node("classify", classify)
builder.add_node("prepare", prepare)
builder.add_edge(START, "classify")
builder.add_edge("classify", "prepare")
builder.add_edge("prepare", END)
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "stream-demo"}}

if __name__ == "__main__":
    for mode, payload in graph.stream({"ticket": "My parcel is late."}, config=config, stream_mode=["updates", "custom"], version="v1"):
        log(f"{mode.upper()} {payload}")
    saved = graph.get_state(config)
    assert "stage" not in saved.values and "reply" in saved.values
    log(f"SAVED keys={sorted(saved.values)} next={saved.next}")
