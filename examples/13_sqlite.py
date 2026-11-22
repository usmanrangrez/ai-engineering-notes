"""Offline teaching example. Reconstructed and verified by the notes author.
No API key, model call, or external side effect is required.
"""
import time

T0 = time.perf_counter()
def log(message):
    print(f"[{time.perf_counter() - T0:6.2f}s] {message}", flush=True)

import argparse
import tempfile
from pathlib import Path
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat(state):
    log(f"chat START messages={len(state['messages'])}")
    return {"messages": [AIMessage(content="What happened to the delivery?")]}

builder = StateGraph(State)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--read", action="store_true")
    parser.add_argument("--db", type=Path, default=Path(tempfile.gettempdir()) / "ai-notes-sqlite-demo.sqlite")
    parser.add_argument("--thread", default="sqlite-demo")
    args = parser.parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": args.thread}}
    with SqliteSaver.from_conn_string(str(args.db)) as saver:
        chatbot = builder.compile(checkpointer=saver)
        if args.write:
            chatbot.invoke({"messages": [HumanMessage(content="My order ID is ORDER-EXAMPLE.")]}, config=config)
        messages = chatbot.get_state(config).values.get("messages", [])
        log(f"SAVED messages={len(messages)}")
        for message in messages:
            print(type(message).__name__, message.content)
