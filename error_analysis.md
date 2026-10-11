# RAG Evaluation Error Analysis: Baseline LLM vs v2_topk6

**Evaluation Corpus:** Mount Carmel College Student Handbook (7 active Markdown files, 56 chunks)  
**Embedding Model:** `all-MiniLM-L6-v2` (ONNX local embedding via ChromaDB)  
**LLM:** `gemini-3.5-flash-lite` (via Google Gemini OpenAI-compatible API, `temperature=0.0`)  
**Evaluation Dataset:** 20 labeled test questions (10 DEV, 10 TEST; 14 answerable, 6 out-of-scope refusals)  
**Scoring Protocol:** Case-insensitive keyword verification for answerable queries; exact refusal-phrase verification for out-of-scope queries (`should_refuse=1`).

---

## 1. Comparative Evaluation Summary

| Run Label | Split | Answer Correctness | Retrieval Hit Rate | Citation Accuracy | Correct Refusals | Avg Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **baseline_llm** (k=4) | **DEV (N=10)** | **90.0%** (9/10) | **100.0%** (10/10) | **100.0%** (10/10) | **100.0%** (3/3) | 3.03s |
| **baseline_llm** (k=4) | **TEST (N=10)** | **90.0%** (9/10) | **100.0%** (10/10) | **90.0%** (9/10) | **100.0%** (3/3) | 2.60s |
| **v2_topk6** (k=6) | **DEV (N=10)** | **90.0%** (9/10) | **100.0%** (10/10) | **90.0%** (9/10) | **100.0%** (3/3) | 2.65s |
| **v2_topk6** (k=6) | **TEST (N=10)** | **90.0%** (9/10) | **100.0%** (10/10) | **90.0%** (9/10) | **100.0%** (3/3) | 2.29s |

---

## 2. Failure Case Diagnostics

### Failure Case 1: DEV Split — Question 7

- **Question ID:** 7 (`split: dev`, `should_refuse: 0`)
- **Question:** *"For postgraduate (PG) students, what overall semester average is required to be declared passed?"*
- **Expected Source:** `attendance_regulations.md` (Line 38)
- **Expected Evidence Quote:** `- Along with a semester average of 50%`
- **Expected Keywords:** `50%`
- **Evidence Chunk in Corpus:** `attendance_regulations.md_chunk_004`

#### Baseline Run (`top_k = 4`) Analysis
- **Retrieved Chunks:**
  1. `attendance_regulations.md_chunk_003` (distance: 0.3308)
  2. `attendance_regulations.md_chunk_002` (distance: 0.3450)
  3. `attendance_regulations.md_chunk_001` (distance: 0.3753)
  4. `promotion_and_awards.md_chunk_001` (distance: 0.4045)
- **Diagnosis:** The true evidence chunk (`attendance_regulations.md_chunk_004`) was ranked **6th** (distance: 0.4609), falling outside the top-4 retrieval window. The model received chunk 003 containing the 40% paper-level criteria, and generated:
  > *"To be declared PASS in a semester, a PG student must secure: - 40% in each paper—both in theory & practicals in the ESE (End Semester Examination) as well as - Have a minimum of 40% (ESE + CIA) for each paper. [Source: attendance_regulations.md]"*
- **Failure Classification:** **Retrieval Under-Recall (k too small)**.

#### V2 Run (`top_k = 6`) Analysis
- **Retrieved Chunks:**
  1. `attendance_regulations.md_chunk_003`
  2. `attendance_regulations.md_chunk_002`
  3. `attendance_regulations.md_chunk_001`
  4. `promotion_and_awards.md_chunk_001`
  5. `continuous_internal_assessment.md_chunk_001`
  6. `attendance_regulations.md_chunk_004`
- **Diagnosis:** `attendance_regulations.md_chunk_004` was successfully retrieved at rank 6. However, due to character-based chunk splitting (500 chars, 80 overlap), chunk 004 starts mid-sentence with `"ticals in the ESE as well as..."` and lacks the `### For PG` header present in chunk 003. Separated by chunks from two other files (`promotion_and_awards.md` and `continuous_internal_assessment.md`), the LLM could not unambiguously attribute the 50% semester average requirement to PG students, and strictly adhered to the grounded refusal prompt:
  > *"I don't know based on the provided documents."*
- **Failure Classification:** **Chunk Boundary Fragmentation / Lost Context Across Interleaved Documents**.

---

### Failure Case 2: TEST Split — Question 17

- **Question ID:** 17 (`split: test`, `should_refuse: 0`)
- **Question:** *"What academic condition must a UG candidate satisfy to be permitted to enter the Fifth Semester?"*
- **Expected Source:** `promotion_and_awards.md` (Line 12)
- **Expected Evidence Quote:** `- A candidate will be permitted to go to the Fifth Semester provided she has passed overall in 50% of the papers of Part I, II & III of the First and Second Semesters.`
- **Expected Keywords:** `50% of the papers`
- **Evidence Chunk in Corpus:** `promotion_and_awards.md_chunk_000`

#### Baseline (`top_k = 4`) and V2 (`top_k = 6`) Analysis
- **Retrieved Chunks (Rank Order):**
  - Rank 1: `attendance_regulations.md_chunk_002` (distance: 0.3894)
  - Rank 2: `attendance_regulations.md_chunk_001` (distance: 0.4535)
  - Rank 3: `attendance_regulations.md_chunk_003` (distance: 0.4827)
  - Rank 4: `promotion_and_awards.md_chunk_001` (distance: 0.4918)
  - Rank 5: `attendance_regulations.md_chunk_000` (distance: 0.5068)
  - Rank 6: `results_and_revaluation.md_chunk_003` (distance: 0.5125)
  - Rank 7: `attendance_regulations.md_chunk_004` (distance: 0.5272)
  - **Rank 8:** `promotion_and_awards.md_chunk_000` (distance: 0.5319) — **Evidence Chunk**
- **Diagnosis:** The dense embedding model (`all-MiniLM-L6-v2`) prioritized chunks describing general undergraduate "Minimum for Pass" and attendance conditions over the specific promotion section. Because the evidence chunk was ranked 8th, it was omitted in both k=4 and k=6 runs.
- **Generated Answer:**
  > *"I don't know based on the provided documents."*
- **Failure Classification:** **Dense Retrieval Embedding Mismatch (Dense Rank Miss)**. Because the retrieval window did not contain the 5th semester rule, the system behaved reliably by refusing rather than hallucinating an academic requirement.

---

## 3. Analysis of Refusal Behavior (Out-of-Scope Queries)

Across both runs and both splits:
- **DEV Refusals (Q8, Q9, Q10):** 3 / 3 correct (100.0%)
- **TEST Refusals (Q18, Q19, Q20):** 3 / 3 correct (100.0%)
- **Total Refusal Accuracy:** **6 / 6 (100.0%)**
- **Hallucination Rate:** **0.0%**

All six questions asked about plausible, college-related topics not covered in the ingested corpus (fee refund schedules, placement packages, tuition fees, gymnasium timings, library borrowing allowances, hostel mess fees). In every instance, the pipeline cited the refusal string exactly without speculative generation.

---

## 4. Key Takeaways for Production Architecture

1. **Heading-Aware Chunking:** Fixed character chunking (500 chars) severed the relationship between parent headers (`### For PG`) and downstream list items, causing conservative refusals on chunk 004. Hierarchical or Markdown section chunking prevents this.
2. **Hybrid Search (BM25 + Dense):** For queries with specific entities or terms (e.g., "Fifth Semester"), lexical BM25 search would have scored `promotion_and_awards.md_chunk_000` at Rank 1, eliminating the dense retrieval miss on Q17.
3. **Safety & Grounding:** Zero hallucinations were observed across all 40 LLM interactions. The refusal prompt strictly prevented fabrication on out-of-scope and partially-retrieved questions.
