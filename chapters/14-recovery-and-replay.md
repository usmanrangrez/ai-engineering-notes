## What it is and why it matters
A tracking service can fail after ticket preparation completed. Starting from scratch repeats work unnecessarily. A checkpointer can restore committed progress and schedule unfinished work.

## Lab: file 16
```bash
uv run 16_support_ticket_recovery.py
```
```text
▶ FIRST INVOCATION
prepare_ticket START
prepare_ticket DONE prepared=True
check_tracking START prepared=True
check_tracking FAILED simulated service outage
GRAPH STOPPED Simulated tracking service outage
SAVED STATE {'ticket': 'My parcel is late.', 'prepared': True}
NEXT NODES ('check_tracking',)
SERVICE RESTORED
▶ RESUME unfinished work
check_tracking START prepared=True
check_tracking DONE tracking='IN_TRANSIT'
finish_ticket START tracking='IN_TRANSIT'
finish_ticket DONE
FINAL STATE {'ticket': 'My parcel is late.', 'prepared': True, 'tracking': 'IN_TRANSIT', 'resolution': 'Ask the courier to investigate the delay.'}
```
Preparation ran once; tracking ran twice. This demo caught an exception and resumed in the same Python process using InMemorySaver. It was not a simulated operating-system process restart.

## Three invocation cases
| Call | Meaning |
| --- | --- |
| invoke(new_input, thread_config) | Apply new input and start execution from the graph entry |
| invoke(None, latest_thread_config) | Continue pending work from the latest checkpoint; a completed graph has no pending work |
| invoke(None, historical_snapshot.config) | Replay execution after the selected earlier checkpoint |

None means no new input. It does not mean the result is None. The restored execution can return a full state dictionary.

## Replay selection
```python
before_chat = None
for snapshot in chatbot.get_state_history(chat_config):
    if snapshot.next == ("chat_node",):
        before_chat = snapshot
        break

if before_chat is not None:
    result = chatbot.invoke(None, config=before_chat.config)
```
Historical config includes a checkpoint address. A thread-only config selects the latest state. Replaying after a selected checkpoint can repeat LLM/tool calls; it does not simply display a cached transcript.

## Pending writes
If parallel work partially succeeds, checkpoint pending writes can preserve successful task outputs so they need not repeat on resume. That is distinct from choosing an arbitrary historical checkpoint for replay. A node re-executed after failure begins at its function entry, not the exact failed Python statement.

## In production
External side effects need idempotency. Restoring state does not guarantee an email, refund request, or job post executes exactly once. Define recovery and compensation around business actions.

## Interview questions
::: question What if invoke(None) targets a completed latest checkpoint?
There is no pending node to execute. It is not automatically a new conversation turn.
:::
::: question Why does recovery differ from retrying the whole script?
Recovery uses saved execution progress and pending work. Restarting the entire workflow may repeat successful actions.
:::

## References
- [Checkpointers and replay](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- [Time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
