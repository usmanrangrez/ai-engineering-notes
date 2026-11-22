## What it is and why it matters
Editing an order ID after the model answered should regenerate the answer using the correction. Merely changing the last completed state does not necessarily schedule the chat node again.

## Mechanism
```text
Earlier checkpoint: Human(original ID), next=chat_node
        |
        +-- update_state with Human(same message ID, new content)
                  |
                  +-- new checkpoint, next=chat_node
                            |
                            +-- invoke(None, edited checkpoint config)
```
**Fork:** a new continuation from existing saved history. The earlier checkpoints remain available.

## Important code shape
```python
old_message = before_chat.values["messages"][-1]
edited_message = HumanMessage(
    id=old_message.id,
    content="My order ID is ORDER-CORRECTED.",
)
fork_config = chatbot.update_state(
    before_chat.config,
    {"messages": [edited_message]},
)
result = chatbot.invoke(None, config=fork_config)
```
Same message ID makes add_messages replace the item. A new message ID would normally append another message instead. update_state applies normal field reducer semantics; it is not an unrestricted mutation of old checkpoint rows.

## Lab: file 17
```bash
uv run 17_support_chatbot_edit.py
```
```text
You: /thread edit-demo-1
You: My order ID is ORDER-ORIGINAL.
You: /edit My order ID is ORDER-CORRECTED.
EDIT BEFORE id=<MESSAGE_ID> content='My order ID is ORDER-ORIGINAL.'
EDIT AFTER  id=<MESSAGE_ID> content='My order ID is ORDER-CORRECTED.'
FORK messages=1 next=('chat_node',)
▶ CONTINUE edited checkpoint
chat_node START messages=1
EDIT DONE messages=2
AI: Could you let me know what issue you’re experiencing with order ORDER-CORRECTED?
```
The message ID is the same on both lines. The fork had one message before generation and two afterwards. Exact personal and business identifiers are replaced with placeholders.

## Why select the pre-chat checkpoint?
The latest completed checkpoint normally has next=(). Updating it can be attributed to a completed node and leave no next execution. This lab chose the checkpoint with next=('chat_node',) so the intended regeneration was explicit.

## What !r means
In `f"content={message.content!r}"`, !r formats the value using repr(). It makes quotes and escape characters visible for inspection. It does not alter the stored content.

## In production
Define whether editing an earlier message discards or branches later turns. Our CLI edited the most recent user turn. Editing arbitrary old messages requires an explicit policy for subsequent state and external actions.

## Interview questions
::: question Does changing content alone replace a message?
Replacement depends on matching message IDs with add_messages. Without that identity, the update may be a new message.
:::
::: question Does replay undo an already-sent email?
No. External effects require business-level handling; checkpoint branching does not reverse them.
:::

## References
- [Time travel and state updates](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
- [add_messages](https://reference.langchain.com/python/langgraph/graph/message/add_messages)
