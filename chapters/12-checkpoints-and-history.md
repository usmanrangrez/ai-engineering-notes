## What it is and why it matters
The chatbot cannot answer a follow-up about an order ID unless previous messages are restored. A checkpointer saves graph state by thread and by execution boundary.

```python
checkpointer = InMemorySaver()
chatbot = builder.compile(checkpointer=checkpointer)
chat_config = {"configurable": {"thread_id": "support-demo-1"}}

result = chatbot.invoke(
    {"messages": [HumanMessage(content=user_input)]},
    config=chat_config,
)
```
**Thread ID:** identifies one conversation/execution history. It is not a Python execution thread, a message ID, an order ID, or an authorization credential.

## Lab: saved context and history
```text
You: My order ID is ORDER-EXAMPLE.
chat_node START messages=1
graph DONE messages=2
You: What is my order ID?
chat_node START messages=3
graph DONE messages=4
AI: Your order ID is ORDER-EXAMPLE.
```
The second node input was prior human + prior AI + new human. The final response made four stored messages.

```text
You: /history
SAVED HISTORY thread='support-demo-1' messages=4
1. HumanMessage: My order ID is ORDER-EXAMPLE.
2. AIMessage: Could you let me know what issue you’re experiencing with order ORDER-EXAMPLE?
3. HumanMessage: What is my order ID?
4. AIMessage: Your order ID is ORDER-EXAMPLE.
```

## One snapshot versus an iterator
```python
snapshot = chatbot.get_state(chat_config)
messages = snapshot.values.get("messages", [])

for snapshot in chatbot.get_state_history(chat_config):
    print(snapshot.metadata.get("step"), snapshot.next)
```
get_state returns one StateSnapshot. get_state_history returns an iterator of snapshots, newest first; list(...) materializes it. Both read state without calling the model.

| Snapshot field | Meaning |
| --- | --- |
| values | Saved state dictionary |
| next | Tuple of scheduled node names; () means no pending nodes |
| config | Thread and checkpoint address |
| metadata | Execution metadata, including graph step |

## Super-step receipt
```text
CHECKPOINT step=1 messages=2 next=()
CHECKPOINT step=0 messages=1 next=('chat_node',)
CHECKPOINT step=-1 messages=0 next=('__start__',)
```
These are execution-boundary snapshots, not simply one checkpoint per visible diagram label. The initial/input boundary and the completed-node boundary are distinct.

## Selecting a checkpoint without hiding Python syntax
```python
before_chat = None
for snapshot in chatbot.get_state_history(chat_config):
    if snapshot.next == ("chat_node",):
        before_chat = snapshot
        break
```
The tuple's trailing comma makes it a one-item tuple. snapshot.next is an attribute, not the built-in next(). A compact equivalent is next((s for s in history if condition), None); prefer the loop when debugging.

## In production
InMemorySaver survives repeated calls in the same process but not process exit. Checkpointing is thread-scoped memory, not automatically cross-thread long-term memory. Keep application ownership checks outside the assumption that knowing an ID grants access.

## Interview questions
::: question Is get_state_history the chat message history?
No. It is graph checkpoint history. Each snapshot may contain a growing conversation in its values.
:::
::: question Why do two user turns not mean step=2?
A turn can involve several super-steps. A Python turn counter and graph step metadata measure different things.
:::

## References
- [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)
