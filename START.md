# Start here

## Who this course is for
You can write Python functions and use dictionaries, but LLM applications and graph workflows may be new. Start with chapter 1 and read in order. You do not need to watch the linked videos first. The website explains the concepts; the course links provide attribution and an optional second explanation.

An **LLM**, or large language model, generates responses from supplied input. An **agent** is an application in which a model can help decide actions, often by requesting tools. A **tool** is an operation supplied by application code, such as looking up a policy; the model does not become the Python function. A **workflow** specifies how work proceeds. We first build workflows so that an agent's state, tools, and control flow will not be mysterious later.

## How to use a chapter
1. Read the concrete problem and the three concepts before opening the complete file.
2. Predict the result of the small test. Write the node order, changed keys, or message count you expect.
3. Run the offline example, then compare your output with the author verification trace. Timings can differ.
4. Read the historical lab receipt and its mistakes. These are real learning evidence, not an output template you must reproduce exactly.
5. Try the exercises, then open the self-check answer. Be able to explain the mechanism before advancing.

**Read** marks a topic studied in the original learner's course record; it does not mean you personally completed it. **Planned** pages are outlines, not finished lessons. There are 20 teaching chapters available now; tools, RAG, approval, deployment, and later projects remain planned. The 54 notes chapters are not the playlist's video numbers or the original 18-topic syllabus.

## Set up an isolated learning project
A **virtual environment** keeps a project's Python dependencies separate. A **package manager** installs those dependencies. These labs use uv, which also runs scripts in the project's environment. Install uv using its [official installation guide](https://docs.astral.sh/uv/getting-started/installation/) if needed.

[Terminal] Clone the public repository and enter it:

```bash
git clone https://github.com/usmanrangrez/ai-engineering-notes.git
cd ai-engineering-notes
```

[Terminal] Create a local environment and install the offline lab dependencies:

```bash
uv venv --python 3.14
uv pip install langgraph langchain-core pydantic langgraph-checkpoint-sqlite
```

The Python baseline is 3.14 for the lab code; the static website builder separately supports Python 3.10+. Dependency versions used during author verification are recorded in the [verification receipts](examples/VERIFIED.md). These commands install compatible packages available to you; they do not promise identical dependency versions forever. Save a lockfile when turning a lab into a reproducible application.

[Terminal] Run the first lab:

```bash
uv run examples/01_async.py
```

These **offline labs** call no model service and need no API keys. SQLite examples write a small test database; their commands explain where. They do not access your existing project data. For the restart demonstration:

```bash
uv run examples/13_sqlite.py --write
uv run examples/13_sqlite.py --read
```

The first command saves a turn, and the second reads it in a new process. Repeating write adds another turn to the same test conversation; use a different --thread value to create a fresh case.

## Adding a real model later
A **provider** hosts the model's inference service. The original learner used Groq through LangChain's ChatGroq integration. An **API key** is a credential that authorizes requests. Never put one into a public repository, website form, issue, trace metadata, or pasted debugging output.

The offline examples intentionally separate graph mechanics from model quality, latency, and rate limits. Once the mechanics work, install the integration:

```bash
uv pip install langchain-groq python-dotenv
```

Create an untracked .env in your local working directory with your real key. The example here is a placeholder, not a working key:

```dotenv
GROQ_API_KEY=<YOUR_LOCAL_GROQ_KEY>
```

`python-dotenv` can load those settings into the process. This model setup is an integration excerpt, not a measured new live-model lab:

```python
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    reasoning_effort="low",
    max_tokens=1000,
    max_retries=1,
    timeout=30,
)
```

`model` selects the provider's model ID. `reasoning_effort` selects a supported reasoning setting. `max_tokens` limits generated output tokens; a **token** is a model-processing text unit, not necessarily one word. The cap can cut a sentence short. `timeout` bounds a client wait; it is not a graph step limit. `max_retries=1` permits a client retry; it does not mean zero retries. If a graph retry policy also exists, consider the combined attempts and choose one owner of backoff deliberately.

The model ID and low-effort option were checked against Groq's documentation on 2026-11-22. Model availability, access and limits can change; consult [supported models](https://console.groq.com/docs/models) and [reasoning settings](https://console.groq.com/docs/reasoning) before a new integration. No paid model call was made while expanding this site.

## Read outputs as evidence
A **receipt** is an observed output supporting a specific claim. A message count of four proves four messages were saved in that test; it does not establish semantic correctness of every response. A score proves the checks implemented by its evaluator. A Mermaid diagram shows declared topology, whereas a trace shows the path an invocation actually took.

The code blocks in a lesson may be small excerpts. Each downloadable offline file includes its imports and graph wiring. New offline traces were executed by the notes author; historical model outputs came from the learner's hand-run labs. The distinction is stated on every chapter with a new example.

## Begin the course
Start with [Async Python](chapters/01-async-python.html), then [Pydantic contracts](chapters/02-pydantic-contracts.html), then [models, tools, and framework roles](chapters/03-interfaces-and-tools.html). If a graph concept becomes unclear, return to [state, nodes, and edges](chapters/04-graph-core.html). Use the chapter index to resume later.

## References
- [Python tutorial](https://docs.python.org/3.14/tutorial/)
- [uv environments](https://docs.astral.sh/uv/pip/environments/)
- [LangGraph graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [ChatGroq integration](https://docs.langchain.com/oss/python/integrations/chat/groq)

Facts last checked: 2026-11-22.
