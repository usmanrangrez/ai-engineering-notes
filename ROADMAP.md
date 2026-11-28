# One working roadmap

Follow DSwithBappy’s course order as the backbone, insert prerequisites where needed, and audit anything the original syllabus leaves uncovered. Do not restart completed lessons.

## Current checkpoint
Completed: Chatbot Parts 1–9 through Tool calling, ReAct loop, RAG in LangGraph (Part 8), Human-in-the-Loop (Part 9 / `#28`), Persistence (`#26` redo), and Streaming (`#27` refresh). Active next: build an **integrated resume-worthy portfolio project** combining all studied concepts and **deploy it** (Videos 22–23: Docker, GitHub Actions, AWS, Render).

## Original 18-topic checklist
13 of 18 original topics are complete (with `#33` core tracing done and `#34` separate threads done). This is not completion of the larger combined roadmap.

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
| 26 | Persistence and checkpointers | Complete (redone hands-on) |
| 27 | Streaming | Complete (refreshed hands-on) |
| 28 | Human-in-the-loop | Complete |
| 29 | Subgraphs | Planned |
| 30 | Send / map-reduce | Planned |
| 31 | Tool calling as a graph | Complete |
| 32 | ReAct from scratch | Complete |
| 33 | LangSmith observability | Core tracing complete; full evaluation pending |
| 34 | Memory across threads | Separate threads done; shared long-term memory planned |
| 35 | Recruitment capstone | Planned |

## Immediate learning order
1. **Now:** Build one real resume-worthy end-to-end project combining RAG, tools, SQLite persistence, streaming, multi-thread management, LangSmith tracing, and HITL (Chapter 25).
2. **Next:** Deploy the integrated project (Videos 22–23: Docker, GitHub Actions, AWS, Render).
3. **Remaining Core LangGraph:** `#29` Subgraphs, `#30` `Send`/map-reduce, `#34` shared long-term memory (`user_id` / store).
4. **Backend, MCP, Guardrails & Multi-Agent:** FastAPI + PostgreSQL, MCP fundamentals & integration, Guardrails, Supervisor/multi-agent orchestration.
5. **Production & Capstone:** Systematic AI evaluation (hosted LangSmith eval), harness/production loops & ops, `#35` Recruitment Capstone, then optional extensions.

## Later playlist and original-syllabus coverage
FastAPI/PostgreSQL and project architecture; TripMate; MCP fundamentals and application; subgraphs; Send/map-reduce; AgentWriter; guardrails; supervisor patterns; harness/loop engineering; long-term memory; full evaluation experiments; gateways; Corrective RAG; Self-RAG; further project/deployment studies; agentic RAG; FDE delivery; CloudOps; GraphRAG; multimodal RAG; production RAG; voice/vision; Bedrock; production operations; recruitment capstone.

Project videos are architecture studies plus focused implementations. Repeated scaffolding is reviewed briefly. A project is not marked complete merely because a related library was mentioned.

## Course and timestamp policy
[DSwithBappy course playlist](https://www.youtube.com/playlist?list=PLkz_y24mlSJZ9SFlc9O4Q4Grli5SQDbrB)

Verified individual video links start at 00:00. Fine-grained timestamps are added only when verified against the actual transcript/video. Several original attachments have no timestamps; their chapter pages link to the course and explicitly mark exact timestamps unverified. No estimated timestamp is presented as evidence.

## Recruitment capstone
Requirements → draft/refine job description → human approval → posting → application monitoring → assist shortlisting → interview scheduling → offer drafting → renegotiation. Consequential hiring decisions and external actions require deliberate human and authorization boundaries.
