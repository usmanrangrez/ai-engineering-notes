# Author verification receipts

Run on 2026-11-22. These are new offline examples run by the notes author, not additional learner-completed lessons. Timings vary. No model or service call was made.

Environment: langgraph 1.2.24, langgraph-checkpoint-sqlite 3.1.3, langchain-core 1.8.4, pydantic 2.14.4.

## 01_async.py

```text
[  0.03s] policy START
[  0.03s] profile START
[  0.13s] policy DONE
[  0.23s] profile DONE
[  0.23s] RESULTS ['policy', 'profile']
```

## 02_contracts.py

```text
[  0.08s] VALID {'verdict': 'approved', 'score': 8, 'feedback': 'Request the order ID.'}
[  0.08s] REJECTED ('score',) less_than_equal
[  0.08s] REJECTED ('verdict',) literal_error
```

## 03_tools.py

```text
[  0.30s] TOOL lookup_policy ARGS {'category': {'enum': ['refund', 'delivery'], 'title': 'Category', 'type': 'string'}}
[  0.31s] POLICY Ask for the order ID.
[  0.31s] REJECTED literal_error
```

## 04_graph_core.py

```text
[  0.27s] COMPILE (node has not run)
[  0.27s] INVOKE
[  0.27s] classify START ticket='My parcel is late.'
[  0.27s] classify DONE category='delivery'
[  0.27s] FINAL {'ticket': 'My parcel is late.', 'category': 'delivery'}
```

## 05_sequential.py

```text
graph TD;
	__start__ --> classify;
	classify --> retrieve_policy;
	retrieve_policy --> draft_reply;
	draft_reply --> __end__;

[  0.67s] classify START
[  0.67s] classify DONE category='delivery'
[  0.67s] retrieve_policy START category='delivery'
[  0.67s] retrieve_policy DONE policy='Ask for the order ID.'
[  0.67s] draft_reply START policy='Ask for the order ID.'
[  0.67s] draft_reply DONE reply='Please provide your order ID.'
[  0.67s] FINAL keys=['category', 'policy', 'reply', 'ticket'] reply='Please provide your order ID.'
```

## 06_routing.py

```text
[  0.22s] understand DONE category='account'
[  0.22s] ROUTE account
[  0.22s] account_help START
[  0.22s] FINAL Use the official password-reset page.
```

## 07_bounded.py

```text
[  0.23s] check words=6/5 attempts=0/2
[  0.23s] ROUTE repair
[  0.23s] repair START attempt=1
[  0.23s] repair DONE reply='Please provide your order ID'
[  0.23s] check words=5/5 attempts=1/2
[  0.23s] ROUTE finish
[  0.23s] FINAL acceptable=True
```

## 08_parallel.py

```text
[  0.22s] count_characters START
[  0.22s] count_words START
[  0.33s] count_words DONE words=5
[  0.43s] count_characters DONE chars=29
[  0.43s] combine START words=5 chars=29
[  0.43s] FINAL 5 words; 29 characters events=['characters checked', 'words checked']
```

## 10_iterative.py

```text
[  0.22s] check revision=0 score=0/2 violations=['Ask for the order ID.', 'Remove unauthorized refund approval.']
[  0.22s] revise START prompt_hash=ec5a000f
[  0.22s] revise DONE
[  0.22s] check revision=1 score=2/2 violations=[]
[  0.22s] STOP reason=approved
[  0.22s] HISTORY [{'revision': 0, 'reply': 'Your refund is approved.', 'score': 0}, {'revision': 1, 'reply': 'Please provide your order ID so support can check tracking.', 'score': 2}]
```

## 11_messages.py

```text
[  0.22s] chat START messages=1
[  0.22s] chat DONE returning_messages=1
[  0.22s] FINAL messages=2
[  0.22s] chat START messages=1
[  0.22s] chat DONE returning_messages=1
[  0.22s] FINAL messages=2
[  0.22s] SAME-ID replacement count=1 content='new'
```

## 12_persistence.py

```text
[  0.23s] chat START messages=1
[  0.23s] FINAL messages=2
[  0.23s] chat START messages=3
[  0.23s] FINAL messages=4
[  0.23s] CURRENT next=()
[  0.23s] CHECKPOINT step=4 messages=4 next=()
[  0.23s] CHECKPOINT step=3 messages=3 next=('chat',)
[  0.23s] CHECKPOINT step=2 messages=2 next=('__start__',)
[  0.23s] CHECKPOINT step=1 messages=2 next=()
[  0.23s] CHECKPOINT step=0 messages=1 next=('chat',)
[  0.23s] CHECKPOINT step=-1 messages=0 next=('__start__',)
[  0.23s] FRESH THREAD messages=0
```

## 13_sqlite.py

```text
[  0.24s] chat START messages=1
[  0.24s] SAVED messages=2
HumanMessage My order ID is ORDER-EXAMPLE.
AIMessage What happened to the delivery?
[  0.23s] SAVED messages=2
HumanMessage My order ID is ORDER-EXAMPLE.
AIMessage What happened to the delivery?
```

## 14_recovery.py

```text
[  0.23s] prepare START
[  0.23s] tracking START prepared=True
[  0.23s] FAILED Simulated tracking outage
[  0.23s] SAVED prepared=True next=('tracking',)
[  0.23s] RESUME
[  0.23s] tracking START prepared=True
[  0.23s] finish START tracking=IN_TRANSIT
[  0.23s] COUNTS {'prepare': 1, 'tracking': 2, 'finish': 1}
[  0.23s] FINAL Ask the courier to investigate.
```

## 15_edit.py

```text
[  0.23s] chat START messages=1
[  0.23s] ORIGINAL Received: My order ID is ORDER-OLD.
[  0.23s] FORK messages=1 next=('chat_node',)
[  0.23s] chat START messages=1
[  0.23s] EDITED Received: My order ID is ORDER-NEW.
```

## 16_streaming.py

```text
[  0.26s] classify START
[  0.26s] UPDATES {'classify': {'category': 'delivery'}}
[  0.26s] prepare START
[  0.26s] CUSTOM {'stage': 'drafting'}
[  0.31s] CUSTOM {'stage': 'completed'}
[  0.31s] UPDATES {'prepare': {'reply': 'Please provide your order ID.'}}
[  0.31s] SAVED keys=['category', 'reply', 'ticket'] next=()
```

## 17_threads.py

```text
[  0.22s] chat START messages=1
[  0.22s] chat START messages=1
[  0.23s] chat START messages=3
[  0.23s] COUNTS first=4 second=2
[  0.23s] FRESH messages=0 directory=3 first_preserved=True
```

## 20_evaluator.py

```text
[  0.00s] valid {'score': True, 'contains_phrase': True, 'words': 10}
[  0.00s] invalid {'score': False, 'contains_phrase': False, 'words': 5}
[  0.00s] unsafe_but_metric_passes {'score': True, 'contains_phrase': True, 'words': 9}
[  0.00s] A PASS MEASURES THE CHECKS, NOT COMPLETE SAFETY
```
