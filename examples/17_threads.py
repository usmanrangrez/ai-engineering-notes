"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

from uuid import uuid4
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat(state):
    log(f"chat START messages={len(state['messages'])}")
    return {"messages": [AIMessage(content="Message received.")]}

def add_thread(directory, thread_id, title):
    if thread_id not in directory:
        directory[thread_id] = {"title": title}

def load_conversation(chatbot, thread_id):
    return chatbot.get_state({"configurable": {"thread_id": thread_id}}).values.get("messages", [])

def send(chatbot, thread_id, text):
    return chatbot.invoke({"messages": [HumanMessage(content=text)]}, config={"configurable": {"thread_id": thread_id}})

builder = StateGraph(State)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)
chatbot = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":
    directory = {}
    first, second, fresh = str(uuid4()), str(uuid4()), str(uuid4())
    add_thread(directory, first, "Delayed headphones")
    add_thread(directory, second, "Account access")
    add_thread(directory, first, "Duplicate ID")
    assert len(directory) == 2
    send(chatbot, first, "My headphones are late.")
    send(chatbot, second, "I cannot sign in.")
    active = first
    send(chatbot, active, "My order ID is ORDER-EXAMPLE.")
    a, b = len(load_conversation(chatbot, first)), len(load_conversation(chatbot, second))
    log(f"COUNTS first={a} second={b}")
    assert (a, b) == (4, 2)
    add_thread(directory, fresh, "New chat")
    active = fresh
    assert load_conversation(chatbot, active) == []
    assert len(load_conversation(chatbot, first)) == 4
    log(f"FRESH messages=0 directory={len(directory)} first_preserved=True")
