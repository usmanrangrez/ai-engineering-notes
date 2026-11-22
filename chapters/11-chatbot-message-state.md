## What it is and why it matters
A model knows only the messages supplied to that call. Your Python loop running twice does not itself give the second invocation the first invocation's state.

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
