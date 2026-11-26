## What it is and why it matters
An LLM cannot answer questions accurately from private PDFs or internal documents that were not in its training data. **Retrieval-Augmented Generation (RAG)** indexes document chunks as numeric vectors, retrieves the closest original passages for a user's question, and exposes that search as a `rag_tool` inside our LangGraph agent so the model answers from verified evidence with page citations.

## Learn from the beginning
**Prerequisite:** `@tool`, `bind_tools`, `ToolNode`, and `tools_condition` from chapters 21–22.

### Concept 1 — Chunking preserves page offsets and boundary context
A 15-page PDF cannot be stuffed blindly into one search item. We extract each page into a LangChain `Document` carrying `page_content` (`str`) and `metadata` (`{"source": "my_paper.pdf", "page": page_number}`), then split each page with `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len, add_start_index=True)`.

- **Chunk size** caps how many characters each chunk can hold before splitting.
- **Chunk overlap** carries trailing characters from the left chunk into the start of the right chunk so sentences across boundaries are not cut in half.
- **`add_start_index=True`** records each chunk's starting character offset inside its page string so neighbors on the same page can be verified directly with `zip(chunks, chunks[1:])`.

### Concept 2 — Embeddings map meaning to numbers
A **vector** is an ordered Python `list[float]` (like a GPS coordinate `[lat, lon]`, except acting as a "meaning address"). An **embedding** is a vector representing a piece of text for mathematical comparison. Each slot in the list is one **dimension** (`gemini-embedding-001` outputs `3,072` dimensions by default, working together without simple human labels like `"rain"` or `"pizza"`).

Step through the three frames below to see how raw strings become vectors and how retrieval returns the **original text and metadata**—not the raw floats:

::: visual rag-embedding-plot | 3-frame visual: raw texts to 2D plot to closest original text returned

Why do related texts land near each other even when embedded separately? During model training (before our app runs), the embedding model learned patterns that place relevant question–passage pairs close together. In our app, **Google's already-trained model** generates each vector independently, and **our retrieval code** compares them.

> **One strict rule:** You must use the **exact same embedding model** for indexing chunks (`embed_documents`, document mode `RETRIEVAL_DOCUMENT`) and embedding user questions (`embed_query`, query mode `RETRIEVAL_QUERY`). Your **chat model** can be from a different provider (e.g., Groq for chat + Google Gemini for embeddings).

### Concept 3 — How retrieval actually finds original text (two linked tables)
`embed_documents(texts)` only receives plain strings (`list[str]`)—Google's API never sees `metadata`. It guarantees output order matches input order (`0 ↔ 0`, `1 ↔ 1`), so Python (`zip(chunks, vectors)`) and vector stores keep two linked tables aligned by row `id`:

::: visual rag-two-table-retriever | 3-step visual: Vector Index scoring and Docstore lookup

| Feature | **FAISS** (used in Bappy's video) | **Chroma** | **`InMemoryVectorStore`** (`langchain-core`) |
| --- | --- | --- | --- |
| What it is | Fast vector-search library (Table 1); LangChain adds Python docstore (Table 2) | Full local vector database (SQLite-backed) | Built-in exact cosine store in `langchain-core` |
| Persistence | `save_local` / `load_local` (uses Python `pickle` — only load trusted files) | Automatic via `persist_directory` | `dump` / `load` (plain JSON — safe and readable) |
| Why used here | Bappy's Part 8 baseline | Great for CRUD + metadata filters | Zero deprecated packages (`langchain-community` is sunset) and Python 3.14-safe; maps 1-to-1 to FAISS methods |

### Concept 4 — Cosine similarity and the "narrow cone" effect
**Cosine similarity** measures the **angle** between two vectors (`+1.0` = same direction, `0.0` = perpendicular, `-1.0` = opposite). Use the slider and presets below to see why unrelated English text (`"How do I bake pepperoni pizza?"`) scored **`+0.4796`** in our live lab instead of going negative:

::: visual rag-cosine-cone | Interactive cosine similarity angle and narrow-cone visualizer

All normal English sentences share common grammar and vocabulary, so modern embedding models cluster them into one **narrow cone**. Unrelated English topics sit near opposite edges of that cone (`~61° → +0.48`), while a relevant match sits closer inside (`~41° → +0.75`). Because top-`k` search always sorts and returns `k` chunks, an unrelated query still returns `k` low-scoring chunks—never assume `> 0.4` means relevant.

### Concept 5 — Tracing `rag_tool` inside LangGraph
Wrapping vector search in `@tool def rag_tool(query: str) -> str:` plugs retrieval straight into the exact same LangGraph loop from chapters 21–22. Formatting `source` and `page` into the returned string is essential because the chat model only reads `ToolMessage.content`—it never sees `doc.metadata` directly.

Step through all 6 execution steps below to watch which line runs and how `graph.invoke({"messages": [...]})` and node returns append to `state["messages"]` via `add_messages`:

::: visual rag-code-flow | 6-step interactive code flow debugger for 26_support_ticket_rag.py

### Concept 6 — Connecting RAG to a multi-thread chatbot backend
In our standalone script, both halves sit in one file and there is **no checkpointer** (each test prompt starts fresh). In a multi-user chatbot backend (like Bappy's Part 8 backend), those two halves become two separate actions:

```text
  BUTTON 1: "Upload PDF"   (top half of 26_support_ticket_rag.py)
    PdfReader ─▶ split ─▶ embed ─▶ save vector index per thread_id
    (runs ONCE when a PDF is uploaded — no chat LLM call)
                         │
                         ▼
  BUTTON 2: "Send message" (bottom half of 26_support_ticket_rag.py)
    graph.invoke(..., config) ─▶ ask_model ─▶ rag_tool ─▶ cited answer
    (runs on EVERY message; add SQLite checkpointer only when chat memory is needed)
```

Keep the two stores distinct: a **checkpointer** stores conversation `messages` per `thread_id`; a **vector store** stores chunk vectors, original text, and page metadata.

## Historical learner lab record
File: `<PROJECT_ROOT>/support_ticket/26_support_ticket_rag.py` with `my_paper.pdf` (Bappy's rainfall regression paper, Video 20 / Chatbot Part 8).

Command run (installed dependencies, no temporary `--with` flags):
```bash
uv run 26_support_ticket_rag.py
```

### 1. PDF extraction and chunk overlap receipt
```text
PDF PAGES: 15
DOCUMENTS: 15
TOTAL CHUNKS: 44
SAME PAGE: 3
LEFT END: 945 RIGHT START: 800
OVERLAP CHARACTERS: 145
```
`pypdf` emitted an optional `fontTools` font-decoding warning; extraction completed and inspected previews were readable.

### 2. Single-chunk and multi-chunk Gemini embedding receipts
Using `GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")`:
```text
EMBEDDING INPUT: {'source': 'my_paper.pdf', 'page': 3, 'start_index': 0} characters: 945
VECTORS RETURNED: 1
DIMENSIONS: 3072
FIRST FIVE VALUES: [0.0010593326, -0.00050124386, 0.030577552, -0.04921259, -0.0018966125]
```
Passing two chunks (`chunks[2:4]`) changed only the outer list length (`VECTORS RETURNED: 2`), keeping `dims: 3072` per vector and reproducing identical leading floats for `start_index: 0`:
```text
VECTORS RETURNED: 2
PAIRED: {'source': 'my_paper.pdf', 'page': 3, 'start_index': 0} | dims: 3072 | first 3: [0.0010593326, -0.00050124386, 0.030577552]
PAIRED: {'source': 'my_paper.pdf', 'page': 3, 'start_index': 800} | dims: 3072 | first 3: [0.004526384, -0.0038424928, 0.022578163]
```

### 3. Manual cosine similarity and full 44-chunk index receipts
Comparing `embed_query("What regression methods are used for rainfall measurement?")` against `chunks[0]` vs. an unrelated pizza sentence:
```text
QUERY VECTOR DIMS: 3072
SCORE (rainfall chunk 0): 0.7528
SCORE (pizza unrelated): 0.4796
```
Indexing all 44 chunks into `InMemoryVectorStore`, saving to `my_paper_index.json`, and reloading from disk (`0` chunk-embedding API calls on reload):
```text
LOADING INDEX FROM: <PROJECT_ROOT>/support_ticket/my_paper_index.json

--- PAPER QUESTION: What regression methods are used for rainfall measurement? ---
score=0.7812 | page=3 | 'Development of Multiple Combined Regression Methods for Rainfall Measurement...'
score=0.7760 | page=13 | 'task is to find out the best regression technique for the prediction of rain...'
score=0.7702 | page=4 | 'Some of the research has shown some classification method to predict whether...'

--- UNRELATED QUESTION: How do I bake a pepperoni pizza in a home oven? ---
score=0.5353 | page=8 | '... Pre-Processing In machine learning, the data preprocessing is within...'
score=0.5310 | page=9 | 'neighbors[27], five nearest is chosen for every iteration...'
score=0.5282 | page=9 | 'of outliers can cause, they tend to be unaffected by littler UI changes...'
```

### 4. End-to-end LangGraph `rag_tool` receipt (3 paths)
Using `GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")` for retrieval + `ChatGroq(model="openai/gpt-oss-120b", reasoning_effort="low", max_tokens=500)` for reasoning:
```text
=== 1. DIRECT REPLY ===
MESSAGE TYPES: ['HumanMessage', 'AIMessage']
FINAL ANSWER: Hello! How can I help you today?

=== 2. PDF QUESTION ===
MESSAGE TYPES: ['HumanMessage', 'AIMessage', 'ToolMessage', 'AIMessage']
TOOL CALLS: [{'name': 'rag_tool', 'args': {'query': 'regression methods rainfall measurement'}, 'id': '<TOOL_CALL_ID>', 'type': 'tool_call'}]
FINAL ANSWER: Summarized Linear Regression, Multiple Linear Regression (MLR),
Generalized Regression Neural Network (GRNN), Clusterwise Linear Regression (CLR)
[source: my_paper.pdf, p 5] and predictive regression analysis [source: my_paper.pdf, p 4].

=== 3. NO EVIDENCE ===
MESSAGE TYPES: ['HumanMessage', 'AIMessage']
FINAL ANSWER: Stated that the rainfall regression paper does not cover baking pizza.
```
Notice two real behaviors observed in the live receipt:
- In **Path 2**, the Groq chat model rewrote the user's question into concise search keywords (`'regression methods rainfall measurement'`), pulling in **page 5** where specific regression methods were listed.
- In **Path 3**, because `system_instruction` already identified the PDF as a rainfall regression paper, the model skipped `rag_tool` completely for pizza. Testing a *plausible-but-missing* rainfall question is needed to verify post-retrieval refusal after a `ToolMessage`.

## Mistakes and fixes
- **Deprecated `langchain-community` import:** importing `FAISS` from `langchain_community.vectorstores` emitted a sunset `DeprecationWarning`. Switching to `langchain_core.vectorstores.InMemoryVectorStore` removed the deprecated package and avoided Python 3.14 native wheel build issues while keeping the same LangChain vector store API.
- **Duplicate `from_documents` call triggering `429 RESOURCE_EXHAUSTED`:** leaving `InMemoryVectorStore.from_documents(chunks, embeddings)` outside the `else:` branch caused the script to load `my_paper_index.json` *and then* re-embed all 44 chunks anyway, hitting Google's free-tier limit (`100` embed requests/minute). Keeping `from_documents` + `dump` strictly inside `else:` reduced reload runs to `0` chunk-embedding calls.

## In production
Separate ingestion pipelines from chat request handlers, persist vector indexes in an appropriate database (e.g., PostgreSQL/pgvector, Chroma, or managed vector search) when scale or metadata filtering requires it, never treat raw cosine scores as relevance percentages, calibrate thresholds on your specific embedding model, and evaluate retrieval hit rate separately from LLM answer faithfulness.

## Interview questions
::: question Why can two separately embedded texts land near each other in vector space?
The embedding model was pre-trained on large collections of related question–passage pairs to map semantically related text to nearby directions in vector space. At runtime, each string is embedded independently using those learned weights.
:::
::: question Why did an unrelated pizza query score +0.4796 instead of 0.0 or negative?
Modern transformer embeddings exhibit a narrow-cone effect: normal English sentences share common linguistic structure and cluster inside one cone of vector space. Unrelated English pairs sit near opposite edges of that cone (~60 degrees, cosine ~0.48) rather than opposite sides of the sphere.
:::
::: question Why must `rag_tool` format `source` and `page` into its returned string?
The chat model only reads `ToolMessage.content` on its next turn; it cannot inspect Python `Document.metadata` objects directly. Including source and page numbers in the tool output makes citations verifiable.
:::
::: question Why does `InMemoryVectorStore.load(path, embeddings)` still require `embeddings` if chunk vectors are already saved?
Loading from disk skips re-embedding the stored chunks, but the vector store still needs the exact same embedding model at search time to embed incoming user questions into the same vector space.
:::

## References
- [LangGraph Agentic RAG guide](https://docs.langchain.com/oss/python/langgraph/agentic-rag)
- [LangChain Google Generative AI embeddings](https://docs.langchain.com/oss/python/integrations/embeddings/google_generative_ai)
- [Google Gemini Embeddings API](https://ai.google.dev/gemini-api/docs/embeddings)
- [DSwithBappy Part 8 video](https://www.youtube.com/watch?v=p5U6uX7LDE8)
- [Course repository](https://github.com/entbappy/Complete-Agentic-AI-Course)
