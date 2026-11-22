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
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat(state):
    count = len(state["messages"])
    log(f"chat START messages={count}")
    return {"messages": [AIMessage(content=f"I received {count} messages.")]}

builder = StateGraph(State)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)
chatbot = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "persistence-demo"}}

if __name__ == "__main__":
    for text in ["My order ID is ORDER-EXAMPLE.", "What is my order ID?"]:
        result = chatbot.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        log(f"FINAL messages={len(result['messages'])}")
    snapshot = chatbot.get_state(config)
    assert len(snapshot.values["messages"]) == 4
    log(f"CURRENT next={snapshot.next}")
    for saved in chatbot.get_state_history(config):
        log(f"CHECKPOINT step={saved.metadata.get('step')} messages={len(saved.values.get('messages', []))} next={saved.next}")
    other = chatbot.get_state({"configurable": {"thread_id": "fresh-demo"}})
    assert other.values.get("messages", []) == []
    log("FRESH THREAD messages=0")
