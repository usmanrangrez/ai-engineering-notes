"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat(state):
    log(f"chat START messages={len(state['messages'])}")
    text = next(m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage))
    log("chat DONE returning_messages=1")
    return {"messages": [AIMessage(content=f"Received: {text}")]}

builder = StateGraph(State)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)
graph = builder.compile()

if __name__ == "__main__":
    for text in ["My order ID is ORDER-EXAMPLE.", "What is my order ID?"]:
        result = graph.invoke({"messages": [HumanMessage(content=text)]})
        log(f"FINAL messages={len(result['messages'])}")
        assert len(result["messages"]) == 2
    old = [AIMessage(id="answer", content="old")]
    changed = add_messages(old, [AIMessage(id="answer", content="new")])
    assert len(changed) == 1 and changed[0].content == "new"
    log("SAME-ID replacement count=1 content='new'")
