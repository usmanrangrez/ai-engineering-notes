# AI Engineering Notes

A public teaching site for Python, LangGraph and production-oriented AI engineering. Twenty available chapters explain definitions, mental models, small code steps, runnable examples and self-check exercises for readers learning the topic for the first time. Based on DSwithBappy’s course and guided support-ticket labs. Explanations are original; receipts are sanitized historical learner outputs.

Live teaching site: https://usmanrangrez.github.io/ai-engineering-notes/

## Start learning

Open [Start here](https://usmanrangrez.github.io/ai-engineering-notes/start.html) for prerequisites and setup. The [offline examples](examples/) make no model calls; [author verification receipts](examples/VERIFIED.md) distinguish new executed examples from historical learner runs. Planned chapters remain outlines.

## Current checkpoint
Core LangSmith tracing complete. Tool calling in LangGraph is next. 11 of 18 original syllabus topics complete; the expanded roadmap is larger. Evaluation dataset/local metric introduced; experiments pending.

## Build locally
Requires Python 3.10+; no third-party build packages.
```bash
python3 build.py
python3 check.py
python3 -m http.server 8000 --directory site
```
Open http://localhost:8000. GitHub Pages serves the generated site with relative URLs, including under a repository subpath.

## Structure
```text
chapters/              Markdown teaching chapters
examples/              complete offline Python labs and verification receipts
START.md               independent-reader setup and study guide
chapters.json          order, status, course links and summaries
assets/                shared CSS, JavaScript and favicon
build.py               reusable static HTML generator
check.py               link, content, privacy and build checks
site/                  generated, ignored by Git
PROGRESS.md            learning state and preferences
TEACHING.md            filled-in teaching and notes agreement
ROADMAP.md             original and combined coverage
.github/workflows/     GitHub Pages build and deployment
```

## Publish after explicit approval
Create the public repository, commit the reviewed source on main and push only after user approval. In Settings → Pages choose GitHub Actions as the source. The workflow builds and checks the site, uploads site/, and deploys it. Future main pushes update it only after their own approval. Check workflow success and the live URL before reporting publication complete.

## Chapters
| Chapter | Status | Coverage |
| --- | --- | --- |
| [01. Async Python for agents](chapters/01-async-python.md) | Read | Prior completion recorded; original receipt unavailable |
| [02. Pydantic contracts and structured output](chapters/02-pydantic-contracts.md) | Read | Completed hands-on |
| [03. Model interfaces, tools, and framework roles](chapters/03-interfaces-and-tools.md) | Read | Completed hands-on |
| [04. State, nodes, edges, build and compile](chapters/04-graph-core.md) | Read | Completed hands-on |
| [05. Sequential support-ticket workflow](chapters/05-sequential-workflow.md) | Read | Completed hands-on |
| [06. Conditional routing and nested decisions](chapters/06-conditional-routing.md) | Read | Completed hands-on |
| [07. Bounded repair loops and runtime limits](chapters/07-bounded-loops.md) | Read | Completed hands-on |
| [08. Parallel siblings, reducers, and AND-joins](chapters/08-parallel-workflows.md) | Read | Completed hands-on |
| [09. Parallel LLM reviews and structured-output failures](chapters/09-parallel-llm-reviews.md) | Read | Completed hands-on |
| [10. Iterative refinement and hybrid evaluation](chapters/10-iterative-refinement.md) | Read | Completed hands-on |
| [11. Chatbot message state and add_messages](chapters/11-chatbot-message-state.md) | Read | Completed hands-on |
| [12. Persistence, snapshots, and history](chapters/12-checkpoints-and-history.md) | Read | Completed hands-on |
| [13. SQLite persistence across restarts](chapters/13-sqlite-persistence.md) | Read | Completed hands-on |
| [14. Recovery, continuation, and replay](chapters/14-recovery-and-replay.md) | Read | Tutor extension, learner-run recovery lab |
| [15. Edit messages and fork a checkpoint](chapters/15-edit-and-fork.md) | Read | Tutor extension, learner-run edit lab |
| [16. Streaming updates, state, text, and progress](chapters/16-streaming.md) | Read | Completed hands-on |
| [17. Conversation IDs, titles, and switching](chapters/17-conversation-management.md) | Read | Completed hands-on |
| [18. Durable directories and SQLite chat history](chapters/18-durable-conversations.md) | Read | Completed hands-on |
| [19. LangSmith tracing and debugging](chapters/19-langsmith-observability.md) | Read | Completed hands-on |
| [20. Evaluation datasets and a local evaluator](chapters/20-evaluation-introduction.md) | Read | Introduced; dataset and local evaluator only |
| [21. Tool calling in LangGraph](chapters/21-tool-calling.md) | Planned | Not started; scope only |
| [22. Build the model–tool loop](chapters/22-react-loop.md) | Planned | Not started; scope only |
| [23. RAG in LangGraph](chapters/23-rag-in-langgraph.md) | Planned | Not started; scope only |
| [24. Human approval and interrupts](chapters/24-human-in-loop.md) | Planned | Not started; scope only |
| [25. Integrate the support agent](chapters/25-integrated-support-agent.md) | Planned | Not started; scope only |
| [26. Docker, AWS, and GitHub Actions](chapters/26-docker-aws-ci.md) | Planned | Not started; scope only |
| [27. A second deployment route: Render](chapters/27-render.md) | Planned | Not started; scope only |
| [28. FastAPI and PostgreSQL application structure](chapters/28-fastapi-postgres.md) | Planned | Not started; scope only |
| [29. TripMate project study](chapters/29-tripmate.md) | Planned | Not started; scope only |
| [30. MCP fundamentals](chapters/30-mcp.md) | Planned | Not started; scope only |
| [31. MCP integration project](chapters/31-mcp-project.md) | Planned | Not started; scope only |
| [32. Subgraphs and state boundaries](chapters/32-subgraphs.md) | Planned | Not started; scope only |
| [33. Send and dynamic map-reduce](chapters/33-send-map-reduce.md) | Planned | Not started; scope only |
| [34. AgentWriter project study](chapters/34-agentwriter.md) | Planned | Not started; scope only |
| [35. Guardrails and action constraints](chapters/35-guardrails.md) | Planned | Not started; scope only |
| [36. Supervisor and multi-agent orchestration](chapters/36-supervisor.md) | Planned | Not started; scope only |
| [37. Harness engineering](chapters/37-harness.md) | Planned | Not started; scope only |
| [38. Production loop engineering](chapters/38-production-loops.md) | Planned | Not started; scope only |
| [39. Memory across conversations](chapters/39-long-term-memory.md) | Planned | Not started; scope only |
| [40. Systematic AI evaluation](chapters/40-evaluation-experiments.md) | Planned | Not started; scope only |
| [41. LLM gateways and usage controls](chapters/41-llm-gateway.md) | Planned | Not started; scope only |
| [42. Corrective RAG](chapters/42-corrective-rag.md) | Planned | Not started; scope only |
| [43. Self-reflective RAG](chapters/43-self-rag.md) | Planned | Not started; scope only |
| [44. Self-correcting multi-agent deployment](chapters/44-self-correcting-deployment.md) | Planned | Not started; scope only |
| [45. Agentic RAG with search tools](chapters/45-agentic-rag.md) | Planned | Not started; scope only |
| [46. FDE workflow and delivery project](chapters/46-fde.md) | Planned | Not started; scope only |
| [47. CloudOps Sentinel project study](chapters/47-cloudops.md) | Planned | Not started; scope only |
| [48. GraphRAG with Neo4j](chapters/48-graphrag.md) | Planned | Not started; scope only |
| [49. Multimodal RAG](chapters/49-multimodal-rag.md) | Planned | Not started; scope only |
| [50. Production agentic RAG project](chapters/50-production-rag.md) | Planned | Not started; scope only |
| [51. Voice and vision project study](chapters/51-voice-vision.md) | Planned | Not started; scope only |
| [52. Bedrock-based RAG integration](chapters/52-bedrock.md) | Planned | Not started; scope only |
| [53. Operate the application in production](chapters/53-production-operations.md) | Planned | Not started; scope only |
| [54. Recruitment-agent capstone](chapters/54-recruitment-capstone.md) | Planned | Not started; scope only |

## Sources and evidence
See [ABOUT.md](ABOUT.md) for provenance, sanitization and limitations, [ROADMAP.md](ROADMAP.md) for course mapping, and [PROGRESS.md](PROGRESS.md) for current status. Video links start at verified 00:00 where an individual video was resolved; missing precise chapter timestamps are explicitly marked unverified.

## Attribution
Course: [DSwithBappy Complete Agentic AI Course](https://www.youtube.com/playlist?list=PLkz_y24mlSJZ9SFlc9O4Q4Grli5SQDbrB). [Course repository](https://github.com/entbappy/Complete-Agentic-AI-Course).

Written with AI help. Documented lab receipts were run by hand by the learner; unavailable receipts, reconstructed snippets and planned work are labeled. Personal identifiers and credentials are placeholders.
