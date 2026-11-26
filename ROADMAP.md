# One working roadmap

Follow DSwithBappy’s course order as the backbone, insert prerequisites where needed, and audit anything the original syllabus leaves uncovered. Do not restart completed lessons.

## Current checkpoint
Completed: Tool calling, ReAct loop, and RAG in LangGraph (DSwithBappy Video 20 / Part 8). Next: redo **Persistence (#26)** properly (checkpointers, SQLite, replay, checkpoint editing), then move to **Human-in-the-Loop** (Video 21 / Part 9 / `#28`). Evaluation datasets and a local evaluator were introduced; no full experiment has been run. UI work is deferred until project integration.

## Original 18-topic checklist
11 of 18 original topics are complete (with `#26` Persistence marked undone for a proper redo, `#33` core tracing done, and `#34` separate threads done). This is not completion of the larger combined roadmap.

| Original topic | Scope | Status |
| --- | --- | --- |
| 18 | Async programming | Complete |
| 19 | Pydantic | Complete |
| 20 | LangChain versus LangGraph | Complete |
| 21 | Core components | Complete |
| 22 | Sequential workflow | Complete |
| 23 | Conditional workflow and bounded loops | Complete |
| 24 | Parallel workflow | Complete |
| 25 | Iterative workflow | Complete |
| 26 | Persistence and checkpointers | Undone — redo next before HITL |
| 27 | Streaming | Complete |
| 28 | Human-in-the-loop | Planned (after Persistence redo) |
| 29 | Subgraphs | Planned |
| 30 | Send / map-reduce | Planned |
| 31 | Tool calling as a graph | Complete |
| 32 | ReAct from scratch | Complete |
| 33 | LangSmith observability | Core tracing complete; full evaluation pending |
| 34 | Memory across threads | Separate threads done; shared long-term memory planned |
| 35 | Recruitment capstone | Planned |

## Immediate learning order
1. Redo Persistence properly (checkpointers, SQLite, replay, checkpoint editing — Chapters 12–15).
2. Human-in-the-loop interrupts, approval, rejection, and edit/resume (Video 21 / Part 9).
3. Integrate the support agent, add meaningful evaluation checks, and deploy (Docker, AWS, GitHub Actions, Render).

## Later playlist and original-syllabus coverage
FastAPI/PostgreSQL and project architecture; TripMate; MCP fundamentals and application; subgraphs; Send/map-reduce; AgentWriter; guardrails; supervisor patterns; harness/loop engineering; long-term memory; full evaluation experiments; gateways; Corrective RAG; Self-RAG; further project/deployment studies; agentic RAG; FDE delivery; CloudOps; GraphRAG; multimodal RAG; production RAG; voice/vision; Bedrock; production operations; recruitment capstone.

Project videos are architecture studies plus focused implementations. Repeated scaffolding is reviewed briefly. A project is not marked complete merely because a related library was mentioned.

## Course and timestamp policy
[DSwithBappy course playlist](https://www.youtube.com/playlist?list=PLkz_y24mlSJZ9SFlc9O4Q4Grli5SQDbrB)

Verified individual video links start at 00:00. Fine-grained timestamps are added only when verified against the actual transcript/video. Several original attachments have no timestamps; their chapter pages link to the course and explicitly mark exact timestamps unverified. No estimated timestamp is presented as evidence.

## Recruitment capstone
Requirements → draft/refine job description → human approval → posting → application monitoring → assist shortlisting → interview scheduling → offer drafting → renegotiation. Consequential hiring decisions and external actions require deliberate human and authorization boundaries.
