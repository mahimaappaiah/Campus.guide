# Mount Carmel College RAG Document Assistant

A Retrieval-Augmented Generation (RAG) question-answering system built on official, publicly available Mount Carmel College policy documents. It retrieves grounded context from a local vector store, generates answers via an LLM, cites the source file for every factual claim, and refuses with a fixed phrase when information is absent from the corpus.

---

## Configuration & Chunking

All chunk sizes and overlaps are measured in **characters** (not words or tokens):

- `CHUNK_SIZE_CHARS`: 500 characters
- `CHUNK_OVERLAP_CHARS`: 80 characters
- `TOP_K_RETRIEVAL`: 4 chunks (baseline) / 6 chunks (v2)
- Vector Store: ChromaDB
- Embedding Model: `all-MiniLM-L6-v2` (ONNX runtime, local)
- Generator LLM: `gemini-3.5-flash-lite` (via Google Gemini OpenAI-compatible API, `temperature=0.0`)

---

## Corpus (7 active documents)

All text is verbatim content extracted from official public pages and PDFs published by Mount Carmel College (`mccblr.edu.in`). Provenance and retrieval dates are tracked in `docs/SOURCES.md`.

Active documents:
- `attendance_regulations.md` &rarr; https://mccblr.edu.in/examination-centre/attendance/
- `code_of_conduct.md` &rarr; https://mccblr.edu.in/wp-content/uploads/2026/08/Code-of-Conduct-Students-2026-27.pdf
- `continuous_internal_assessment.md` &rarr; https://mccblr.edu.in/examination-centre/cia/
- `end_semester_examinations.md` &rarr; https://mccblr.edu.in/examination-centre/ese/
- `grievance_redressal_policy.md` &rarr; https://mccblr.edu.in/wp-content/uploads/2026/01/Grievance-Policy-2024.pdf
- `promotion_and_awards.md` &rarr; https://mccblr.edu.in/examination-centre/promotion-awards/
- `results_and_revaluation.md` &rarr; https://mccblr.edu.in/examination-centre/results-revaluation/

Excluded files (`docs_excluded/`):
- `anti_drug_policy.md` — Scanned PDF where only 2 of 6 pages had selectable text; excluded to prevent OCR artifacts.
- `hostel_regulations.md` — Web page contained only website navigation boilerplate with no policy text.
- `library_guidelines.md` — Page listed electronic journal subscriptions and databases rather than actionable borrowing rules.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Set OPENAI_API_KEY, OPENAI_BASE_URL, and LLM_MODEL in .env

# 3. Index corpus into ChromaDB
python ingest.py

# 4. Query the system
python ask.py "What is the minimum attendance percentage required for undergraduate students?"

# 5. Run evaluation harness
python evaluate.py baseline_llm
python evaluate.py v2_topk6 --top_k 6

# 6. Run test suite & corpus verification
python -m pytest tests/ -v
python verify_corpus.py
```

---

## Evaluation Results

Evaluation is measured on **20 labeled questions** (split into 10 DEV and 10 TEST items; 14 answerable questions and 6 out-of-scope refusal questions).

Scoring protocol:
- **Answerable questions:** Case-insensitive keyword matching against verifiable factual terms.
- **Out-of-scope questions:** Exact match with the system refusal string: `"I don't know based on the provided documents."`
- **Citation accuracy:** Verifies that the expected source document appears in the generated citation.

### Experimental Results

| Metric | baseline_llm (k=4) DEV | baseline_llm (k=4) TEST | v2_topk6 (k=6) DEV | v2_topk6 (k=6) TEST |
| :--- | :--- | :--- | :--- | :--- |
| **Answer Correctness** | **90.0%** (9/10) | **90.0%** (9/10) | **90.0%** (9/10) | **90.0%** (9/10) |
| **Retrieval Hit Rate** | **100.0%** (10/10) | **100.0%** (10/10) | **100.0%** (10/10) | **100.0%** (10/10) |
| **Citation Accuracy** | **100.0%** (10/10) | **90.0%** (9/10) | **90.0%** (9/10) | **90.0%** (9/10) |
| **Correct Refusals** | **100.0%** (3/3) | **100.0%** (3/3) | **100.0%** (3/3) | **100.0%** (3/3) |
| **Average Latency** | 3.03s | 2.60s | 2.65s | 2.29s |

*For deep dive on individual test failures and chunk fragmentation analysis, see `error_analysis.md`.*

---

## Project Structure

```
rag-portfolio/
├── common.py           # Shared constants, paths, ChromaDB client
├── ingest.py           # Document chunker and vector indexer
├── ask.py              # Retrieval & LLM answer generation pipeline
├── evaluate.py         # Automated evaluation harness with latency tracking
├── verify_corpus.py    # Corpus audit and verification script
├── tests.csv           # 20 labeled evaluation questions with evidence line quotes
├── error_analysis.md   # Root cause diagnostics for retrieval and generation misses
├── docs/               # 7 active verbatim Markdown policy documents
├── docs_excluded/      # Excluded documents with documented limitations
└── tests/
    └── test_core.py    # Pytest test suite
```
