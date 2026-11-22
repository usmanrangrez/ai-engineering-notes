"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from typing import Literal, NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    reply: str
    attempts: int
    max_repairs: int
    word_limit: int
    words: NotRequired[int]

def check(state):
    words = len(state["reply"].split())
    log(f"check words={words}/{state['word_limit']} attempts={state['attempts']}/{state['max_repairs']}")
    return {"words": words}

def route(state) -> Literal["finish", "repair", "limit_exceeded"]:
    if state["words"] <= state["word_limit"]:
        label = "finish"
    elif state["attempts"] >= state["max_repairs"]:
        label = "limit_exceeded"
    else:
        label = "repair"
    log(f"ROUTE {label}")
    return label

def repair(state):
    attempt = state["attempts"] + 1
    log(f"repair START attempt={attempt}")
    # Artificial mechanical repair, not safe production writing.
    reply = " ".join(state["reply"].split()[:-1])
    log(f"repair DONE reply={reply!r}")
    return {"reply": reply, "attempts": attempt}

builder = StateGraph(State)
builder.add_node("check", check)
builder.add_node("repair", repair)
builder.add_edge(START, "check")
builder.add_conditional_edges("check", route, {"finish": END, "repair": "repair", "limit_exceeded": END})
builder.add_edge("repair", "check")
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"reply": "Please provide your order ID now", "attempts": 0, "max_repairs": 2, "word_limit": 5}, config={"recursion_limit": 20})
    assert result["attempts"] == 1 and result["words"] == 5
    log(f"FINAL acceptable={result['words'] <= result['word_limit']}")
