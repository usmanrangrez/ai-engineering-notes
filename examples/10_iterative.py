"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

import operator
from hashlib import sha256
from typing import Annotated, Literal, TypedDict, NotRequired
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    reply: str
    revisions: int
    max_revisions: int
    violations: NotRequired[list[str]]
    history: Annotated[list[dict], operator.add]

def check(state):
    text = state["reply"].casefold()
    violations = []
    if "order id" not in text:
        violations.append("Ask for the order ID.")
    if "refund is approved" in text:
        violations.append("Remove unauthorized refund approval.")
    score = 2 - len(violations)
    log(f"check revision={state['revisions']} score={score}/2 violations={violations}")
    return {"violations": violations, "history": [{"revision": state["revisions"], "reply": state["reply"], "score": score}]}

def route(state) -> Literal["finish", "revise"]:
    if not state["violations"] or state["revisions"] >= state["max_revisions"]:
        log(f"STOP reason={'approved' if not state['violations'] else 'budget'}")
        return "finish"
    return "revise"

def revise(state):
    prompt = f"CURRENT: {state['reply']} FEEDBACK: {state['violations']}"
    log(f"revise START prompt_hash={sha256(prompt.encode()).hexdigest()[:8]}")
    # A deterministic stand-in proves state flow, not LLM quality.
    reply = "Please provide your order ID so support can check tracking."
    log("revise DONE")
    return {"reply": reply, "revisions": state["revisions"] + 1}

builder = StateGraph(State)
builder.add_node("check", check)
builder.add_node("revise", revise)
builder.add_edge(START, "check")
builder.add_conditional_edges("check", route, {"finish": END, "revise": "revise"})
builder.add_edge("revise", "check")
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"reply": "Your refund is approved.", "revisions": 0, "max_revisions": 2, "history": []}, config={"recursion_limit": 20})
    assert [row["score"] for row in result["history"]] == [0, 2]
    log(f"HISTORY {result['history']}")
