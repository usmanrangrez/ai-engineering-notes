## What it is and why it matters
A model knows only the messages supplied to that call. Your Python loop running twice does not itself give the second invocation the first invocation's state.

::: mental-model LLMs are completely stateless HTTP functions
An LLM API has zero built-in memory of Turn 1. "Memory" in a chatbot simply means your application resends `[Human1, AI1, Human2]` on Turn 2. `MessagesState` uses the **`add_messages` reducer** so returning `{"messages": [response]}` appends new messages by ID (or replaces an existing message when IDs match).
:::

::: warning A reducer merges within one state—it is NOT cross-call persistence
`add_messages` merges updates during a run, but without a **checkpointer** (Chapter 12) or passing the full history list yourself, a second `graph.invoke(...)` call starts from an empty list.
:::

## Learn from the beginning
**Prerequisite:** nodes and state updates. Your goal is to draw the exact list of messages sent to a model on each conversation turn.

### Concept 1 — A model request receives messages, not your whole application
A **conversation turn** is one user contribution and the application's response. A **message** has a role and content. `HumanMessage` represents user input; `AIMessage` represents assistant output; `SystemMessage` supplies application instructions. These are Python message classes, not names of graph nodes.

```python
from langchain_core.messages import HumanMessage, AIMessage
messages = [
    HumanMessage(content="My order ID is ORDER-EXAMPLE."),
    AIMessage(content="What happened to the delivery?"),
    HumanMessage(content="What is my order ID?"),
]
```

If you send only the last message, the order ID is not available in that request. The model may guess, ask again, or behave inconsistently. **The application must supply context; a repeated call does not automatically carry your earlier input.**

### Concept 2 — add_messages merges message updates by identity
```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

`BaseMessage` is the common parent type of these message objects. `Annotated` carries metadata that LangGraph reads as the reducer. `add_messages` appends newly identified messages and replaces a matching message when an update uses an existing ID. Plain list addition does not provide that identity-aware replacement behavior.

The node should return only its new assistant response: `{"messages": [response]}`. Returning the entire old history as well is unnecessary and can create incorrect accumulation when using a different reducer. A message ID identifies one message; a thread ID identifies the graph history containing many messages.

### Concept 3 — In-call state and cross-call persistence are different
```text
One invocation:
new human message --> chat node --> human + assistant in output

Another invocation without restored history:
new human message --> chat node --> new human + new assistant
```

A reducer merges updates within the state the execution has. It does not search previous process calls for a conversation. To continue across invocations, manually send the accumulated list or configure a checkpointer; the next lesson uses a checkpointer.

## Build it in small pieces
Start with a deterministic echo node: find the newest human message and return one `AIMessage`. Wire START → chat_node → END. Verify one input message becomes two output messages. This tests graph/message plumbing independently of model behavior. The [offline message lab](../examples/11_messages.py) provides the complete version.

When adding a model, construct the prompt explicitly:

```python
system_instruction = "Use only the supplied conversation. Do not invent order details."
model_messages = [SystemMessage(content=system_instruction), *state["messages"]]
response = llm.invoke(model_messages)
return {"messages": [response]}
```

The `*` expands the saved list into the new list after the system message. The system instruction is sent to the model but is not automatically stored in graph state because the node returns only response. `response.content` gives text here; the whole response object preserves message metadata.

## Check your understanding
Predict the input/output message counts for two fresh invocations with one human message each and no checkpointer. Then run the offline lab.

::: question Exercise receipt: inspect the model context
Print only each message's type and sanitized content before the call. Identify whether the order ID is actually in the second request.
:::
::: question Exercise receipt: message identity
Use add_messages to update an AIMessage with the same ID. Show that the message changes without the list growing.
:::


## Runnable example and verified trace

Offline lab (no API key or model call required; [setup guide](../start.html)):

[Open the complete Python file](../examples/11_messages.py). Run from the repository root:

```bash
uv run examples/11_messages.py
```

::: question Complete runnable file — open after the small-step explanation
```python
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
```
:::

Author verification output (elapsed times vary):

```text
[  0.22s] chat START messages=1
[  0.22s] chat DONE returning_messages=1
[  0.22s] FINAL messages=2
[  0.22s] chat START messages=1
[  0.22s] chat DONE returning_messages=1
[  0.22s] FINAL messages=2
[  0.22s] SAME-ID replacement count=1 content='new'
```

| Trace observation | What it establishes |
| --- | --- |
| Both separate invocations finish with messages=2 | No checkpointer restored the first invocation into the second. |
| SAME-ID replacement count=1 | add_messages replaced the message with the matching ID. |


## Self-check answer

Try the exercise predictions before opening this explanation.

::: question Explain the mechanism and check your prediction
Without restored input history, each fresh invocation starts with one human message and produces two messages. add_messages replaces a matching ID; it does not look up prior calls by itself. The model can only use context the application supplies.
:::

## Historical learner lab record

```python
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```
**Message object:** a typed conversation item such as HumanMessage, AIMessage, or SystemMessage. add_messages merges message updates and uses message IDs to replace matching items rather than blindly appending everything.

## One turn
```python
def chat_node(state: ChatState) -> dict:
    system_instruction = "Use only the supplied conversation."
    messages = [SystemMessage(content=system_instruction), *state["messages"]]
    response = llm.invoke(messages)
    return {"messages": [response]}
```
The node returns only its new response. LangGraph merges it into state. The system instruction is included in the model input but is not stored in the messages field by this node.

## Lab: file 14 before persistence
```bash
uv run 14_support_chatbot.py
```
```text
You: My order ID is ORDER-EXAMPLE.
chat_node START messages=1
graph DONE turn=1 messages=2
AI: Could you tell me what issue you’re experiencing with order ORDER-EXAMPLE?

You: What is my order ID?
chat_node START messages=1
graph DONE turn=2 messages=2
AI: Could you please provide your order ID so I can assist you further?
```
The order identifier was replaced with a placeholder. The second messages=1 was the decisive evidence: the model was not supplied the earlier turn.

## Why a reducer alone did not solve it
add_messages merges the state supplied to a graph run. To continue across independent invocations, application code must pass previous state or the graph must restore it from a checkpointer. A reducer is a merge rule, not persistent storage.

## In production
Keep system instructions, conversation storage, and display history distinct. Streamlit session_state preserves UI values across reruns in a session; it is not a substitute for a durable backend. We built a minimal UI and explicitly deferred UI specialization.

## Interview questions
::: question Why return one AIMessage rather than the full message history?
The reducer merges the new item. Returning already-stored messages unnecessarily complicates accumulation and replacement behavior.
:::
::: question Does ending a graph erase its returned state?
No. END terminates execution. A future invocation only gets that history if the application supplies or restores it.
:::

## References
- [Message state and reducers](https://docs.langchain.com/oss/python/langgraph/graph-api#working-with-messages-in-graph-state)
- [add_messages reference](https://reference.langchain.com/python/langgraph/graph/message/add_messages)
