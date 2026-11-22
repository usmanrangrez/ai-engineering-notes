"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

import sys
from typing import Literal, NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    ticket: str
    category: NotRequired[str]
    reply: NotRequired[str]

def understand(state):
    text = state["ticket"].casefold()
    category = "account" if "password" in text else "delivery" if "parcel" in text else "other"
    log(f"understand DONE category={category!r}")
    return {"category": category}

def route(state) -> Literal["clarify", "account", "policy"]:
    label = {"other": "clarify", "account": "account", "delivery": "policy"}[state["category"]]
    log(f"ROUTE {label}")
    return label

def ask_clarification(state):
    log("ask_clarification START")
    return {"reply": "What issue do you need help with?"}

def account_help(state):
    log("account_help START")
    return {"reply": "Use the official password-reset page."}

def retrieve_policy(state):
    log("retrieve_policy START")
    return {"reply": "Please provide your order ID."}

builder = StateGraph(State)
builder.add_node("understand_ticket", understand)
for name, action in [("ask_clarification", ask_clarification), ("account_help", account_help), ("retrieve_policy", retrieve_policy)]:
    builder.add_node(name, action)
    builder.add_edge(name, END)
builder.add_edge(START, "understand_ticket")
builder.add_conditional_edges("understand_ticket", route, {"clarify": "ask_clarification", "account": "account_help", "policy": "retrieve_policy"})
graph = builder.compile()

if __name__ == "__main__":
    ticket = sys.argv[1] if len(sys.argv) > 1 else "I forgot my password"
    result = graph.invoke({"ticket": ticket})
    log(f"FINAL {result['reply']}")
