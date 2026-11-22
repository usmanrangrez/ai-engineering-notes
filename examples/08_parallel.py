"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

import operator
from typing import Annotated, NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    reply: str
    words: NotRequired[int]
    chars: NotRequired[int]
    summary: NotRequired[str]
    events: Annotated[list[str], operator.add]

def count_words(state):
    log("count_words START")
    time.sleep(.1)
    words = len(state["reply"].split())
    log(f"count_words DONE words={words}")
    return {"words": words, "events": ["words checked"]}

def count_characters(state):
    log("count_characters START")
    time.sleep(.2)
    chars = len(state["reply"])
    log(f"count_characters DONE chars={chars}")
    return {"chars": chars, "events": ["characters checked"]}

def combine(state):
    log(f"combine START words={state['words']} chars={state['chars']}")
    return {"summary": f"{state['words']} words; {state['chars']} characters"}

builder = StateGraph(State)
for name, action in [("count_words", count_words), ("count_characters", count_characters), ("combine", combine)]:
    builder.add_node(name, action)
builder.add_edge(START, "count_words")
builder.add_edge(START, "count_characters")
builder.add_edge(["count_words", "count_characters"], "combine")
builder.add_edge("combine", END)
graph = builder.compile()

if __name__ == "__main__":
    result = graph.invoke({"reply": "Please provide your order ID.", "events": []})
    assert result["words"] == 5 and len(result["events"]) == 2
    log(f"FINAL {result['summary']} events={result['events']}")
