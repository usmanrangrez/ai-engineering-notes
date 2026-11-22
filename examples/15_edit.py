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
    log(f"chat START messages={len(state['messages'])}")
    human = next(m for m in reversed(state["messages"]) if isinstance(m, HumanMessage))
    return {"messages": [AIMessage(content=f"Received: {human.content}")]}

builder = StateGraph(State)
builder.add_node("chat_node", chat)
builder.add_edge(START, "chat_node")
builder.add_edge("chat_node", END)
chatbot = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "edit-demo"}}

if __name__ == "__main__":
    original = chatbot.invoke({"messages": [HumanMessage(content="My order ID is ORDER-OLD.")]}, config=config)
    log(f"ORIGINAL {original['messages'][-1].content}")
    before_chat = None
    for snapshot in chatbot.get_state_history(config):
        if snapshot.next == ("chat_node",):
            before_chat = snapshot
            break
    if before_chat is None:
        raise RuntimeError("No pre-chat checkpoint found")
    human = before_chat.values["messages"][0]
    replacement = HumanMessage(id=human.id, content="My order ID is ORDER-NEW.")
    fork_config = chatbot.update_state(before_chat.config, {"messages": [replacement]}, as_node="__start__")
    fork = chatbot.get_state(fork_config)
    log(f"FORK messages={len(fork.values['messages'])} next={fork.next}")
    result = chatbot.invoke(None, config=fork_config)
    assert len(result["messages"]) == 2
    assert "ORDER-NEW" in result["messages"][-1].content
    log(f"EDITED {result['messages'][-1].content}")
