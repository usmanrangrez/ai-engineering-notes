## What it is and why it matters
LLMs face three hard structural limits: their weights freeze at training time (**knowledge cutoff**), they have no access to private internal documents (PDFs, policies, tickets), and stuffing entire books into every prompt blows up cost, latency, and attention quality (**"lost in the middle"**). **Retrieval-Augmented Generation (RAG)** solves this by indexing document chunks as numeric vectors, fetching only the top-`k` relevant original passages at query time, and grounding the LLM's answer in verifiable text with source and page citations.

::: mental-model RAG is an open-book exam instead of memorization
Fine-tuning tries to cram facts into the model's weights. RAG gives the model a fast index to look up the exact pages it needs *right before answering*—so you can update documents in seconds without retraining any model, and cite the exact page every claim came from.
:::

## First-principles theory: the 5 stages of a RAG system

### Stage 1 — Extraction & Chunking Theory
Raw PDFs are binary page layouts, not clean text streams. `PdfReader` extracts text page-by-page into LangChain `Document` objects (`page_content: str`, `metadata: {"source": ..., "page": ...}`).

Why not embed an entire 15-page PDF as one vector?
1. **Embedding dilution:** A single vector trying to summarize 15 pages averages out specific details (like one table on page 5), weakening search precision.
2. **Context budget:** Passing all 15 pages to the LLM wastes tokens and degrades focus.

`RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len, add_start_index=True)` splits text hierarchically (preferring paragraph breaks `\n\n`, then line breaks `\n`, then spaces) while respecting two competing tradeoffs:
- **Too small (e.g., 100 chars):** crisp topic focus, but sentences lose surrounding context (e.g., pronouns like *"it"* or *"this method"* lose their subject).
- **Too large (e.g., 4,000 chars):** preserves context, but dilutes the embedding vector and crowds the LLM prompt.
- **Overlap (`chunk_overlap=200`):** copies trailing characters from the left chunk into the start of the right chunk so facts straddling a boundary remain intact in at least one chunk.

### Stage 2 — Dense Embeddings & Vector Space Geometry
Keyword search (exact string matching) fails whenever the user and the document use different words for the same meaning (*"device measuring precipitation"* vs. *"rain gauge measuring rainfall"*).

- A **vector** is an ordered list of floating-point numbers (`list[float]`) representing a point/direction in space.
- An **embedding** is a vector produced by a neural encoder model so that semantically related texts land near each other.
- Each entry is one **dimension**. `gemini-embedding-001` outputs **3,072 dimensions** by default (and supports **Matryoshka Representation Learning (MRL)**, allowing truncation to `768` or `1536` when storage/speed is constrained). Real dimensions work jointly—individual slots do not have simple human labels like `"rain"` or `"pizza"`.

Step through the 3 frames below to see how raw text strings become vectors and how retrieval hands back **original text and metadata** (never raw floats):

::: visual rag-embedding-plot | 3-frame visual: raw texts to 2D plot to closest original text returned

::: concept Why separately embedded texts land close together
During pre-training (contrastive learning on massive query–passage datasets), the embedding model adjusts its weights so relevant question–passage pairs produce vectors with high similarity while unrelated pairs are pushed apart. At runtime, Google's model embeds each string *independently* using those frozen weights—and related texts still land in the same neighborhood.
:::

**Asymmetric retrieval modes (`embed_documents` vs. `embed_query`):**
Questions are short and interrogative (*"What regression methods..."*), while chunks are long and declarative. Google's `gemini-embedding-001` optimizes vectors for their role:
- `embeddings.embed_documents(texts)` → input `list[str]` → output `list[list[float]]` (`RETRIEVAL_DOCUMENT` mode).
- `embeddings.embed_query(question)` → input `str` → output flat `list[float]` (`RETRIEVAL_QUERY` mode).

::: warning Strict model-compatibility rule
You **must** use the exact same embedding model for indexing documents and embedding queries—different embedding models define incompatible coordinate spaces. Your **chat model**, however, is completely independent (our lab pairs **Google Gemini embeddings** with a **Groq chat model**).
:::

### Stage 3 — Vector Similarity Math & the "Narrow Cone" Effect
How do we score whether two vectors `A` and `B` are close? Three standard metrics exist:

| Metric | Formula intuition | Range | Best used when |
| --- | --- | --- | --- |
| **Cosine similarity** | Angle between vectors: `(A · B) / (‖A‖ · ‖B‖)` | `-1.0` to `+1.0` (higher = closer) | Text retrieval (ignores vector length differences). |
| **Dot product** | `sum(a_i * b_i)` | Unbounded (higher = closer) | Vectors are already unit-normalized (`‖A‖ = ‖B‖ = 1`, where dot product equals cosine!). |
| **Euclidean (L2) distance** | Straight-line distance `sqrt(sum((a_i - b_i)^2))` | `0` to `+∞` (**lower** = closer) | Default in standard FAISS `IndexFlatL2`. |

**Tiny worked example (2D):** Let `Q = [1, 1]` and `P = [2, 2]`:
- Dot product: `1*2 + 1*2 = 4`
- Norms: `‖Q‖ = sqrt(2) ≈ 1.414`, `‖P‖ = sqrt(8) ≈ 2.828`
- Cosine similarity: `4 / (1.414 * 2.828) = 4 / 4 = +1.0` (exact same direction, angle `0°`!).

Now try the interactive angle slider below to understand **anisotropy (the "narrow cone" effect)**—why our live unrelated `"pizza"` query scored **`+0.4796`** instead of `0.0` or negative:

::: visual rag-cosine-cone | Interactive cosine similarity angle and narrow-cone visualizer

::: warning Never treat a cosine score like a relevance percentage
`0.4796` does **not** mean "48% about rainfall." Because normal English sentences share massive linguistic structure, transformer embeddings pack them into a narrow cone where unrelated English pairs sit ~60° apart (`cos ≈ 0.45–0.55`) and real matches jump to `0.70–0.85`. Always calibrate thresholds on *your* model and data—and remember that plain top-`k` search **always** returns `k` chunks even when none are relevant.
:::

### Stage 4 — Indexing, Two Linked Tables & Persistence
Google's `embed_documents(texts)` only receives plain strings (`list[str]`) and never sees `Document.metadata`. Because it guarantees strict **index-order preservation** (`texts[i] ↔ vectors[i]`), `zip(chunks, vectors)` and vector stores maintain **two linked structures** joined by row `id`:

::: visual rag-two-table-retriever | 3-step visual: Vector Index scoring and Docstore lookup

| Store | Architecture | Persistence | Search algorithm & scale |
| --- | --- | --- | --- |
| **`InMemoryVectorStore`** (`langchain-core`) | Python dict holding vectors + `Document`s | `dump()` / `load()` via safe plain JSON | Exact cosine scan; ideal for `<10k` chunks, zero deprecated packages, Python 3.14-safe. |
| **FAISS** *(Bappy Part 8)* | C++ vector index (Table 1) + LangChain Python docstore (Table 2) | `save_local()` / `load_local()` (uses Python `pickle` — only load trusted files) | Exact (`Flat`) or Approximate Nearest Neighbor (`IVF`, `HNSW`) for millions of vectors. |
| **Chroma / pgvector** | Full vector database storing vectors + text + metadata together | Automatic DB persistence | Supports CRUD updates, deletion, and structured metadata filtering (`where tenant_id = ...`). |

**Why `load(path, embeddings)` still requires `embeddings`:** loading from disk skips re-embedding the stored chunks (`0` chunk API calls), but the vector store still needs the exact same embedding model at query time to convert each incoming user question into a vector.

### Stage 5 — Agentic RAG inside LangGraph (`rag_tool`)
Instead of forcing retrieval on every message (even `"Hi!"`), **Agentic RAG** wraps retrieval as a `@tool` (`rag_tool`) inside the exact same LangGraph loop from Chapters 21–22:
- **Direct reply (`"Hi!"`):** LLM skips `rag_tool` → `0` embedding calls → `END`.
- **Query rewriting:** When the LLM decides to search, it can rewrite a wordy user question into crisp search keywords (`"regression methods rainfall measurement"`).
- **Grounded citations:** Because the LLM only reads `ToolMessage.content` (never `Document.metadata` directly), `rag_tool` **must** format `source` and `page` into its returned string.

Step through the 6-step execution debugger below to trace every line of `26_support_ticket_rag.py` and see how `graph.invoke({"messages": [...]})` merges into `MessagesState` via `add_messages`:

::: visual rag-code-flow | 6-step interactive code flow debugger for 26_support_ticket_rag.py

### Separating Ingestion from Chat in a Real Backend
In a standalone script, ingestion and chat live in one file with no checkpointer. In a multi-user chatbot backend (FastAPI / Bappy's Part 8 backend), they split into two actions:

```text
  ACTION 1: "Upload PDF"   (runs ONCE per uploaded file — outside graph.invoke)
    PdfReader ─▶ split ─▶ embed_documents ─▶ persist vector index keyed by thread_id / doc_id
                                     │
                                     ▼
  ACTION 2: "Send message" (runs on EVERY chat turn — inside graph.invoke)
    graph.invoke(..., config) ─▶ ask_model ─▶ rag_tool searches that index ─▶ cited answer
    (+ Checkpointer like SqliteSaver/Postgres ONLY for conversation memory per thread_id)
```

## Historical learner lab record
File: `<PROJECT_ROOT>/support_ticket/26_support_ticket_rag.py` with `my_paper.pdf` (Bappy's rainfall regression paper, Video 20 / Chatbot Part 8). Run with `uv run 26_support_ticket_rag.py`.

### 1. Extraction, chunk overlap, and Gemini embeddings receipts
```text
PDF PAGES: 15 | DOCUMENTS: 15 | TOTAL CHUNKS: 44
SAME PAGE: 3  | LEFT END: 945 | RIGHT START: 800 | OVERLAP CHARACTERS: 145

# Single chunk (chunks[2], page 3, 945 chars)
VECTORS RETURNED: 1 | DIMENSIONS: 3072
FIRST FIVE VALUES: [0.0010593326, -0.00050124386, 0.030577552, -0.04921259, -0.0018966125]

# Two chunks (chunks[2:4]): outer list grew to 2, dimensions stayed 3072
VECTORS RETURNED: 2
PAIRED: {'source': 'my_paper.pdf', 'page': 3, 'start_index': 0}   | dims: 3072 | first 3: [0.0010593326, -0.00050124386, 0.030577552]
PAIRED: {'source': 'my_paper.pdf', 'page': 3, 'start_index': 800} | dims: 3072 | first 3: [0.004526384, -0.0038424928, 0.022578163]
```

### 2. Cosine similarity, full 44-chunk search, and JSON persistence receipts
```text
# Manual cosine similarity (embed_query vs embed_documents)
QUERY VECTOR DIMS: 3072
SCORE (rainfall chunk 0): 0.7528
SCORE (pizza unrelated):  0.4796

# Reloaded from my_paper_index.json (0 chunk API calls)
LOADING INDEX FROM: <PROJECT_ROOT>/support_ticket/my_paper_index.json
PAPER QUESTION:     0.7812 (p.3), 0.7760 (p.13), 0.7702 (p.4)
UNRELATED (pizza):  0.5353 (p.8), 0.5310 (p.9),  0.5282 (p.9)  <- top-k always returns k!
```

### 3. End-to-end LangGraph `rag_tool` receipt (3 paths)
```text
=== 1. DIRECT REPLY ("Hi!") ===
MESSAGE TYPES: ['HumanMessage', 'AIMessage']  (0 tool calls)

=== 2. PDF QUESTION ("What regression methods are used for rainfall measurement?") ===
MESSAGE TYPES: ['HumanMessage', 'AIMessage', 'ToolMessage', 'AIMessage']
TOOL CALLS: [{'name': 'rag_tool', 'args': {'query': 'regression methods rainfall measurement'}, 'id': '<TOOL_CALL_ID>'}]
FINAL ANSWER: Cited Linear Regression, MLR, GRNN, CLR [my_paper.pdf, p 5] and predictive regression analysis [p 4].

=== 3. NO EVIDENCE ("What does the paper say about baking pepperoni pizza?") ===
MESSAGE TYPES: ['HumanMessage', 'AIMessage']
FINAL ANSWER: Declined directly because system_instruction identified the PDF as a rainfall paper.
```

## Mistakes and fixes
- **Deprecated `langchain-community` import:** importing `FAISS` from `langchain_community.vectorstores` triggered a sunset `DeprecationWarning`. Switching to `langchain_core.vectorstores.InMemoryVectorStore` eliminated deprecation warnings and Python 3.14 wheel issues while preserving the exact LangChain vector store API.
- **Duplicate `from_documents` call outside `else:` causing `429 RESOURCE_EXHAUSTED`:** leaving `from_documents(chunks, embeddings)` below the `if index_path.exists():` block re-embedded all 44 chunks on every run, exceeding Google's free-tier `100` embed requests/minute quota. Keeping `from_documents` + `dump` strictly inside `else:` dropped reload runs to `0` chunk API calls.

## In production
::: tip Debugging RAG: always separate Retrieval Failure from Generation Failure
When a RAG answer is wrong, inspect `ToolMessage.content` first:
- **Right chunk was NOT retrieved** → **Retrieval failure** (fix chunking, overlap, embedding model, query rewriting, hybrid BM25 + vector search, or reranking).
- **Right chunk WAS retrieved, yet LLM answered wrong** → **Generation failure** (fix system prompt, citation instructions, or chat model).
Never guess which half broke without inspecting the retrieved chunks.
:::

## Interview questions
::: question Why can two separately embedded texts land near each other in vector space?
During contrastive pre-training, the embedding encoder learned weights that map semantically related question–passage pairs to nearby directions. At runtime, each text is embedded independently using those frozen weights.
:::
::: question Why did an unrelated pizza query score +0.4796 instead of 0.0 or negative?
Because of embedding anisotropy (the narrow-cone effect): normal English texts share strong linguistic structure and occupy one cone of vector space, so unrelated English pairs sit ~60° apart (`cos ≈ 0.48`) rather than 90° or 180°.
:::
::: question Why must `rag_tool` format `source` and `page` into its returned string?
The chat model only reads `ToolMessage.content` on its next turn and never sees Python `Document.metadata` objects directly. Formatting metadata into the tool output enables verifiable citations.
:::
::: question How do you diagnose whether a bad RAG answer is a retrieval bug or a generation bug?
Inspect the exact chunks returned in `ToolMessage` before the final LLM call. If the evidence is missing from the top-`k` chunks, it is a retrieval problem (chunking, embeddings, `k`, hybrid search); if the evidence is present but ignored or distorted, it is a generation/prompting problem.
:::

## References
- [LangGraph Agentic RAG guide](https://docs.langchain.com/oss/python/langgraph/agentic-rag)
- [LangChain Google Generative AI embeddings](https://docs.langchain.com/oss/python/integrations/embeddings/google_generative_ai)
- [Google Gemini Embeddings API](https://ai.google.dev/gemini-api/docs/embeddings)
- [DSwithBappy Part 8 video](https://www.youtube.com/watch?v=p5U6uX7LDE8)
- [Course repository](https://github.com/entbappy/Complete-Agentic-AI-Course)
