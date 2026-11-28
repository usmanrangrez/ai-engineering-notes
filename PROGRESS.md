# Learning progress

Last updated: 2026-11-28

## Current position
All core chatbot building blocks through **Video 21 / Chatbot Part 9** are complete with live receipts:
- **RAG in LangGraph (Video 20 / Part 8):** `26_support_ticket_rag.py`
- **Human-in-the-Loop (Video 21 / Part 9 / `#28`):** `27_support_ticket_hitl.py` (safe tool vs. sensitive `issue_refund` with `interrupt()`, `Command(resume=...)`, and Approve / Edit / Reject paths)
- **Persistence (`#26` — properly redone):** `28_persistence_basics.py` (checkpoints, isolated threads, fault tolerance with `invoke(None)`), `29_persistence_time_travel.py` (time travel + `update_state` fork `4 → 7` checkpoints), and `30_persistence_sqlite.py` (`SqliteSaver` surviving across separate Python processes)
- **Streaming (`#27` — visually refreshed):** `31_streaming_modes.py` (live token chunks, `get_stream_writer()`, combined `["messages", "custom"]`, and `metadata["langgraph_node"]` filtering) + Part 4 multi-thread backend architecture refreshed.

**Next:**
1. Build a **resume-worthy integrated end-to-end project** (Chapter 25 — combining RAG, tools, SQLite persistence, streaming, multi-thread management, LangSmith tracing, and HITL), then **deploy it** (Bappy Videos 22–23: Docker, GitHub Actions, AWS, Render).
2. Continue with remaining core LangGraph (`#29` Subgraphs, `#30` `Send`/map-reduce, `#34` shared long-term memory), then Backend/MCP/Guardrails/Multi-Agent, systematic evaluations, production ops, `#35` Recruitment Capstone, and extensions.

The learner confirmed a two-case LangSmith dataset and ran a local evaluator. No full evaluation experiment was run. Resume that material at systematic evaluation or when the project requires a small pre-deployment check.

## Course backbone
DSwithBappy’s playlist: https://www.youtube.com/playlist?list=PLkz_y24mlSJZ9SFlc9O4Q4Grli5SQDbrB

Backend coverage through numbered video 21 / chatbot Part 9 (persistence, streaming, threads, SQLite, LangSmith, tools/ReAct, RAG, and Human-in-the-Loop) is complete. Next is a resume-worthy integrated project (Chapter 25), then numbered videos 22–23 (Docker/AWS/CI/CD and Render). The larger playlist and extra original topics remain in ROADMAP.md and the Planned chapter pages.

## Original syllabus
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

13/18 original topics fully complete (with #33 core tracing complete and #34 separate threads done). This is not a percentage of the expanded roadmap.

## Notes chapters
- 01. Async Python for agents: Read — Prior completion recorded; original receipt unavailable
- 02. Pydantic contracts and structured output: Read — Completed hands-on
- 03. Model interfaces, tools, and framework roles: Read — Completed hands-on
- 04. State, nodes, edges, build and compile: Read — Completed hands-on
- 05. Sequential support-ticket workflow: Read — Completed hands-on
- 06. Conditional routing and nested decisions: Read — Completed hands-on
- 07. Bounded repair loops and runtime limits: Read — Completed hands-on
- 08. Parallel siblings, reducers, and AND-joins: Read — Completed hands-on
- 09. Parallel LLM reviews and structured-output failures: Read — Completed hands-on
- 10. Iterative refinement and hybrid evaluation: Read — Completed hands-on
- 11. Chatbot message state and add_messages: Read — Completed hands-on
- 12. Persistence, snapshots, and history: Read — Completed hands-on (redone visually with live receipts)
- 13. SQLite persistence across restarts: Read — Completed hands-on (redone across separate processes)
- 14. Recovery, continuation, and replay: Read — Completed hands-on (crash recovery verified live)
- 15. Edit messages and fork a checkpoint: Read — Completed hands-on (time-travel fork visual + receipt)
- 16. Streaming updates, state, text, and progress: Read — Completed hands-on (refreshed with combined modes + node filtering)
- 17. Conversation IDs, titles, and switching: Read — Completed hands-on
- 18. Durable directories and SQLite chat history: Read — Completed hands-on
- 19. LangSmith tracing and debugging: Read — Completed hands-on
- 20. Evaluation datasets and a local evaluator: Read — Introduced; dataset and local evaluator only
- 21. Tool calling in LangGraph: Read — Completed hands-on
- 22. Build the model–tool loop: Read — Completed hands-on
- 23. RAG in LangGraph: Read — Completed hands-on (with interactive visuals)
- 24. Human approval and interrupts: Read — Completed hands-on (Approve, Edit, Reject + interactive visuals)
- 25. Integrate the support agent: Planned — Not started; scope only
- 26. Docker, AWS, and GitHub Actions: Planned — Not started; scope only
- 27. A second deployment route: Render: Planned — Not started; scope only
- 28. FastAPI and PostgreSQL application structure: Planned — Not started; scope only
- 29. TripMate project study: Planned — Not started; scope only
- 30. MCP fundamentals: Planned — Not started; scope only
- 31. MCP integration project: Planned — Not started; scope only
- 32. Subgraphs and state boundaries: Planned — Not started; scope only
- 33. Send and dynamic map-reduce: Planned — Not started; scope only
- 34. AgentWriter project study: Planned — Not started; scope only
- 35. Guardrails and action constraints: Planned — Not started; scope only
- 36. Supervisor and multi-agent orchestration: Planned — Not started; scope only
- 37. Harness engineering: Planned — Not started; scope only
- 38. Production loop engineering: Planned — Not started; scope only
- 39. Memory across conversations: Planned — Not started; scope only
- 40. Systematic AI evaluation: Planned — Not started; scope only
- 41. LLM gateways and usage controls: Planned — Not started; scope only
- 42. Corrective RAG: Planned — Not started; scope only
- 43. Self-reflective RAG: Planned — Not started; scope only
- 44. Self-correcting multi-agent deployment: Planned — Not started; scope only
- 45. Agentic RAG with search tools: Planned — Not started; scope only
- 46. FDE workflow and delivery project: Planned — Not started; scope only
- 47. CloudOps Sentinel project study: Planned — Not started; scope only
- 48. GraphRAG with Neo4j: Planned — Not started; scope only
- 49. Multimodal RAG: Planned — Not started; scope only
- 50. Production agentic RAG project: Planned — Not started; scope only
- 51. Voice and vision project study: Planned — Not started; scope only
- 52. Bedrock-based RAG integration: Planned — Not started; scope only
- 53. Operate the application in production: Planned — Not started; scope only
- 54. Recruitment-agent capstone: Planned — Not started; scope only

## Verified practical receipts
- Sequential ticket → policy → reply; category/policy mismatch diagnosed.
- Conditional clarification/account/negative-diagnosis/urgency branches and bounded repair; recursion-limit failure.
- Parallel siblings, concurrent-write error, reducer, explicit AND-join and unequal-depth dependencies.
- Parallel LLM reviews and case-sensitive structured-output tool-name failure.
- Iterative deterministic and semantic evaluation; paraphrase blind spot; history and bounded revision.
- InMemorySaver turns/history; SQLite restart; checkpoint inspection; failure recovery; edit/fork and replay concepts.
- Streaming updates/values/messages/custom, combined modes and saved final state.
- UUID directory, titles, switching, fresh chats, JSON directory restart and SQLite message restart.
- LangSmith live trace and exact prompt, names/tags/metadata, two-turn thread, failed node, traced Python helper, hidden payloads.
- Dataset two examples visible; local evaluator true/false. Full experiment pending.
- Tool calling (`24_support_ticket_tools.py`): `@tool`, `bind_tools`, `AIMessage.tool_calls`, `ToolMessage.tool_call_id`, `ToolNode`, `tools_condition`, and back edge; greeting 0 calls, `ORD-42` 1 lookup + second model call.
- ReAct loop (`25_support_ticket_react.py`): dependent two-tool chain `ORD-42` → `TRK-8317` → `IN_TRANSIT`; 3 model calls requesting `1, 1, 0` tools with `tools_enabled=False` on call 3.
- RAG in LangGraph (`26_support_ticket_rag.py`): `my_paper.pdf` (15 pages, 44 chunks, page-3 overlap `145` chars), `gemini-embedding-001` (`3072` dims), cosine similarity (`0.7528` rainfall vs `0.4796` pizza), `InMemoryVectorStore` JSON persistence (`my_paper_index.json`), `@tool def rag_tool`, and 3-path LangGraph execution citing `my_paper.pdf` pages 4 and 5.
- Human-in-the-Loop (`27_support_ticket_hitl.py`): 1-node `interrupt()` restart proof, structured dict Approve/Edit/Reject resumes, and 4-path Groq agent (`get_order_status` unpaused vs. `issue_refund` paused with Approve `$120`, Edit `$50`, Reject).
- Persistence redo (`28_persistence_basics.py`, `29_persistence_time_travel.py`, `30_persistence_sqlite.py`): 4-snapshot history & thread isolation, crash recovery via `invoke(None)` skipping `classify`, time-travel fork via `update_state` (`4 → 7` checkpoints), and `SqliteSaver` loading saved state across separate Python processes with 0 nodes run.
- Streaming refresh (`31_streaming_modes.py`): `45` live Groq token chunks, `get_stream_writer()` custom progress events, combined `["messages", "custom"]` stream, and `langgraph_node` filtering hiding internal `classify_node` tokens (`DEL`/`IVERY`).

## Environment record
Use Python and uv in the learner's existing AgenticAI project. Public notes use <PROJECT_ROOT>; no real local path is required. Historical receipts span Python 3.14.4–3.14.6. At the successful LangSmith checkpoint: langchain-core 1.8.4, langsmith 0.16.0, langchain-groq 1.2.1. These are observed versions, not globally pinned latest requirements. The working model was Groq openai/gpt-oss-120b with reasoning_effort=low. The historical qwen reviewer is listed as preview in Groq’s catalog checked on 2026-11-22; its current options/tool behavior were not live-tested during the notes expansion.

## Preferences
Read TEACHING.md. One action per teaching message; small steps; prediction before tests; receipts before advancing; complete files on request; explanation before code; direct respectful language; backend first; distinguish Bappy coverage from additions; prefer interactive visuals; avoid deprecated packages (`langchain-community`) and avoid temporary `uv run --with ...` commands (install needed packages normally instead).

## Public teaching expansion
All 20 studied chapters now include first-time explanations, defined terms, three core concepts, small-step code guidance, exercises and self-check answers. Seventeen reconstructed offline examples were run by the notes author, including SQLite writer/reader in separate processes. Their real outputs are recorded separately from historical learner receipts. This editorial expansion does not mark any future lesson complete. A Start here guide supports independent readers.

## Publication
Public repository name approved: usmanrangrez/ai-engineering-notes. The learner approved the initial commit, push to main, and GitHub Pages publication on 2026-11-22. This approval covers the prepared first publication only; ask again before later commits and pushes. Verify the remote commit and live deployment before reporting success.

On 2026-11-22 the learner explicitly authorized the teaching-expansion update to be committed and published while they are away. This applies to this requested expansion; later unrelated publications still require approval.

## Tools source alignment
Checked Bappy’s actual source on 2026-11-22: LangGraph-Code/Agentic-Chatbot-using-LangGraph/agentic_chatbot_tool_backend.py and notebooks/tools_demo.ipynb in entbappy/Complete-Agentic-AI-Course. Both use bind_tools, add_messages, ToolNode(tools), conditional tools_condition after chat_node, and tools → chat_node. Notebook explores before backend integration; backend adds SQLite persistence. Our manual request/execution/ToolMessage walkthrough precedes that same abstraction. Preserve the pending Step 7 receipt; do not skip directly to the graph or restart definitions.
