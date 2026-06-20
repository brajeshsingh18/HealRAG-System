# HealRAG System

A retrieval-augmented answer engine that audits and repairs its own output before returning it. Every answer is scored for retrieval relevance, hallucination, and quality; if it fails any check, the system diagnoses the root cause, applies a targeted repair, and re-audits — up to a configurable number of attempts — before returning a final, logged answer.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) as a stateful, cyclic graph rather than a linear chain, with a Streamlit frontend for live inspection of the pipeline as it runs.

---

## Why this exists

Most RAG demos stop at "retrieve, then generate." This project treats that as the first draft, not the final answer. A second layer — the **audit loop** — checks the draft against three independent criteria, and a third layer — the **repair loop** — fixes the specific thing that's wrong rather than blindly regenerating from scratch.

## How it works

```
START → retrieve → generate → audit ──┬──→ verdict ──┬──→ PASS → log → finalize → save → END
                                       │              │
                          (retrieval_score ≤ 2)       └──→ FAIL → root cause → log → repair ──┐
                                       │                                                        │
                                       └──→ finalize (insufficient context)         back to audit ←┘
                                                                              (until max_retries reached)
```

1. **Retrieve** — pull the top-k relevant chunks for the query from a FAISS vector store.
2. **Generate** — produce a draft answer grounded in the retrieved context.
3. **Audit** — three checks run independently:
   - **Retrieval Auditor** — scores 1–10 whether the retrieved documents actually support answering the question.
   - **Hallucination Checker** — verdict (`SUPPORTED` / `HALLUCINATED`) plus a confidence score, checked against the retrieved context only.
   - **Quality Auditor** — scores completeness, clarity, correctness, relevance, and actionability.
4. **Verdict** — a rule-based gate combines all three signals into `PASS` / `FAIL`. All three must clear a threshold; a weighted composite score is also required to pass.
5. **Root Cause Analysis** — on `FAIL`, an LLM call diagnoses the *primary* root cause (`RETRIEVAL_FAILURE`, `GENERATION_HALLUCINATION`, or `LOW_ANSWER_QUALITY`) and recommends one of four repair actions.
6. **Repair** — applies the recommended fix:
   - `QUERY_REWRITE_AND_RETRIEVE` — rewrites the query and re-retrieves from scratch.
   - `REGENERATE_WITH_CONTEXT_CONSTRAINTS` — regenerates the answer with stricter grounding rules.
   - `EXPAND_AND_REWRITE` — improves completeness, clarity, and depth without changing the facts.
   - `ACCEPT` — passes the answer through unchanged.
7. **Loop or finalize** — the repaired answer goes back through the audit step. This repeats until the verdict passes or `max_retries` is reached, at which point the run finalizes and every attempt is written to an append-only audit log.

If retrieval quality is too low to answer the question at all (`retrieval_score ≤ 2`), the pipeline short-circuits straight to finalization rather than wasting repair attempts on an unanswerable query.

## Architecture

```
app/
├── graph.py                 # LangGraph state machine — nodes, conditional edges, compiled workflow
├── state.py                 # Shared TypedDict state passed between every node
├── verdict_of_issue.py      # Rule-based PASS/FAIL gate combining all three audit signals
├── agents/
│   ├── generator.py         # LLM client + answer generation
│   ├── root_cause.py        # Diagnoses why an answer failed and recommends a repair action
│   └── repair.py            # Executes the recommended repair (rewrite / regenerate / expand)
├── auditors/
│   ├── retrieval.py         # Scores retrieval relevance
│   ├── hallucination.py     # Checks groundedness against retrieved context
│   └── quality.py           # Scores completeness, clarity, correctness, relevance, actionability
├── retrieval/
│   ├── ingest.py            # Chunks and embeds source documents into a FAISS index
│   └── retriever.py         # Similarity search against the FAISS index
└── data/                    # Source documents, FAISS index, saved graph diagrams

frontend/
└── streamlit_app.py         # Live pipeline trace, audit history, analytics, graph visualization

logs/
└── audit_logs.json          # Append-only record of every query, attempt, verdict, and final answer
```

### State

Every node reads from and writes to a single shared state object (`app/state.py`):

```python
class State(TypedDict):
    query: str
    documents: List[Document]
    answer: str
    retrieval_score: int
    hallucination_status: Literal["SUPPORTED", "HALLUCINATED"]
    hallucination_confidence: float
    quality_score: int
    verdict: Literal["PASS", "FAIL"]
    primary_root_cause: Literal["RETRIEVAL_FAILURE", "GENERATION_HALLUCINATION", "LOW_ANSWER_QUALITY"]
    recommended_action: Literal["QUERY_REWRITE_AND_RETRIEVE", "REGENERATE_WITH_CONTEXT_CONSTRAINTS", "EXPAND_AND_REWRITE", "ACCEPT"]
    retries_count: int
    max_retries: int
    audit_record: dict
```

### Audit log format

Every query produces a record like this, with one entry per attempt:

```json
{
  "query": "What is Machine Learning?",
  "attempts": [
    {
      "attempt_no": 1,
      "verdict": "FAIL",
      "retrieval_score": 7,
      "hallucination_status": "SUPPORTED",
      "quality_score": 6,
      "primary_root_cause": "LOW_ANSWER_QUALITY",
      "recommended_action": "EXPAND_AND_REWRITE"
    },
    {
      "attempt_no": 2,
      "verdict": "PASS",
      "retrieval_score": 7,
      "hallucination_status": "SUPPORTED",
      "quality_score": 6
    }
  ],
  "final_verdict": "PASS",
  "total_attempts": 2,
  "total_repairs": 1
}
```

## Frontend

The Streamlit app (`frontend/streamlit_app.py`) is a single-file dashboard with five views:

- **Overview** — what the system does, at a glance.
- **Ask a Question** — submit a query and watch the pipeline run live: each node lights up as it executes, with retrieval/hallucination/quality scores streaming in as they're produced.
- **Audit History** — browse, search, and filter every past query and its full attempt history.
- **Analytics** — pass rate, root-cause frequency, and score trends across repair attempts, charted with Plotly.
- **Pipeline Graph** — the actual compiled LangGraph topology, rendered from `workflow.get_graph().draw_mermaid()` — not a static image, the real graph structure.

## Tech stack

| Layer | Tool |
|---|---|
| Orchestration | LangGraph (stateful, cyclic graph) |
| LLM | Groq (`llama-3.3-70b-versatile`) via `langchain-groq` |
| Embeddings | `BAAI/bge-base-en-v1.5` via `langchain-huggingface` |
| Vector store | FAISS |
| Structured outputs | Pydantic schemas via `with_structured_output` |
| Frontend | Streamlit |
| Charts | Plotly |

## Getting started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_key_here
```

### 3. Build the vector index

Place a source PDF at `app/data/docs/`, then run the ingest script **from inside `app/`** — it uses paths relative to that directory:

```bash
cd app
python retrieval/ingest.py
cd ..
```

This chunks the document, embeds it, and saves a FAISS index to `app/data/faiss/`.

> **Note:** `app/retrieval/retriever.py` also loads the FAISS index using a path relative to `app/` (`"data/faiss"`). The Streamlit frontend (`frontend/streamlit_app.py`) sets its working directory to the **project root**, not `app/`, so that `logs/audit_logs.json` resolves correctly — which means `retriever.py`'s relative FAISS path will *not* resolve correctly when run through the frontend as-is. Either update `app/retrieval/retriever.py` and `app/retrieval/ingest.py` to use absolute paths (e.g. via `pathlib.Path(__file__).parent`), or place the FAISS index at `<project_root>/data/faiss` instead of `<project_root>/app/data/faiss`. See [Roadmap](#roadmap-future-work).

### 4. Run the pipeline directly (optional)

```bash
cd app
python graph.py
cd ..
```

### 5. Launch the frontend

```bash
streamlit run frontend/streamlit_app.py
```

## Roadmap / future work

- **Fix relative path resolution between `app/` and the project root.** `app/retrieval/ingest.py` and `app/retrieval/retriever.py` use paths relative to `app/`, while `frontend/streamlit_app.py` runs with the project root as its working directory (so that `logs/audit_logs.json` resolves correctly). This mismatch means the FAISS index won't be found when retrieval runs through the frontend unless the paths are made absolute or the index is relocated. Switching to `pathlib.Path(__file__).parent`-based paths in `ingest.py`/`retriever.py` would resolve this regardless of working directory.
- **Validate the auditors against a labeled eval set.** Scores currently come from LLM-as-judge calls with no held-out ground truth to measure agreement against. Planned next step: build a small manually-graded benchmark and measure how closely the retrieval/hallucination/quality auditors agree with human judgment, so the scores are validated rather than just self-reported.
- **Cost and latency tracking.** Each repair attempt multiplies LLM calls; surfacing token usage and per-query cost in the Analytics view would make the tradeoffs of the retry loop visible.
- **Swap the vector store for something horizontally scalable** (e.g. Qdrant, Weaviate) if moving beyond a single-document FAISS index.
- **CI-integrated regression tests** for the auditors and verdict logic, so prompt changes don't silently shift scoring behavior.

## License

No license has been added yet — all rights reserved by default until one is chosen.
