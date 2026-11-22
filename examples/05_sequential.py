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
    policy: NotRequired[str]
    reply: NotRequired[str]

def classify(state):
    log("classify START")
    category = "delivery" if "parcel" in state["ticket"].casefold() else "other"
    log(f"classify DONE category={category!r}")
    return {"category": category}

def retrieve_policy(state):
    log(f"retrieve_policy START category={state['category']!r}")
    policy = {"delivery": "Ask for the order ID.", "other": "Ask for details."}[state["category"]]
    log(f"retrieve_policy DONE policy={policy!r}")
    return {"policy": policy}

def draft_reply(state):
    log(f"draft_reply START policy={state['policy']!r}")
    reply = "Please provide your order ID." if state["category"] == "delivery" else "Please describe the issue."
    log(f"draft_reply DONE reply={reply!r}")
    return {"reply": reply}

builder = StateGraph(State)
for name, action in [("classify", classify), ("retrieve_policy", retrieve_policy), ("draft_reply", draft_reply)]:
    builder.add_node(name, action)
builder.add_edge(START, "classify")
builder.add_edge("classify", "retrieve_policy")
builder.add_edge("retrieve_policy", "draft_reply")
builder.add_edge("draft_reply", END)
graph = builder.compile()

if __name__ == "__main__":
    print(graph.get_graph().draw_mermaid(with_styles=False))
    result = graph.invoke({"ticket": "My parcel is late."})
    log(f"FINAL keys={sorted(result)} reply={result['reply']!r}")
    assert result["policy"] == "Ask for the order ID."
