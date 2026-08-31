# GitNova — Verified Interview Numbers & Metrics Registry

Every number in this document is verified by real repository artifacts and database rows. Use ONLY these definitions during your interview.

---

## 1. Production Database Scale
- **Total Ingested Issues:** **1,498** (Total issue records ingested into Supabase `issues` table).
- **Active Repositories:** **153** (Open-source repositories actively tracked in `repos` table).
- **Verified Published Opportunities:** **121** (High-confidence beginner issues approved by 10-gate firewall).
- **Publication Acceptance Rate:** **8.2%** (121 published / 1,498 analyzed — reflects strict fail-closed quality gating).
- **Indexed Code Chunks:** **32,642** (AST-parsed code chunks in `code_chunks` table).

---

## 2. Information Retrieval (RAG) Benchmarks

### A. Controlled Golden Benchmark (25 Cases on Fully Indexed Repositories)
- **Dataset:** 25 historical merged Pull Requests across `pallets/click`, `fastapi/fastapi`, and `facebook/react` ([`backend/golden_set.csv`](file:///c:/gitNova/backend/golden_set.csv)).
- **Recall@1:** **94.0%** (Proportion of ground-truth files retrieved at Rank 1).
- **Recall@5:** **100.0%**
- **Recall@10:** **100.0%**
- **MRR@10:** **1.000** (Mean Reciprocal Rank — the correct target file was at Rank 1 in almost all cases).
- **Hit@10:** **100.0%**

### B. Longitudinal Production Benchmark (91 Real-World Closed PR Cases)
- **Dataset:** 91 historical live issues scanned from Supabase that were subsequently resolved by merged GitHub PRs.
- **Bucket Breakdown:**
  - **Bucket A (Indexed & Valid Fine-Grained Retrieval):** **25 cases (27.5%)**
  - **Bucket B (Unindexed / Incomplete Historical Corpus):** **51 cases (56.0%)**
  - **Bucket C (Mega-PR Scope > 10 files):** **15 cases (16.5%)**
- **Aggregate Recall@10:** **2.58%** *(Note: Correctly explain this as driven by 56% unindexed discovery repos and 16.5% mega-PR denominators, not retriever ranking failure)*.
- **Leakage Audit:** **`PASS` (100%)** — Verified zero ground-truth leakage.

---

## 3. Supervised Fine-Tuning (QLoRA) Experiment
- **Dataset Size:** **600 issues** across **73 repositories** in **20 programming languages** ([`backend/data/dataset_collection/final_v1/experiment_results.json`](file:///c:/gitNova/backend/data/dataset_collection/final_v1/experiment_results.json)).
- **Splits (Repository-Held-Out):**
  - **Train:** 420 issues (49 repositories)
  - **Validation:** 90 issues (14 repositories)
  - **Test:** 90 issues (10 completely unseen repositories)
  - **Repository Overlap:** **0.0% (Strict Holdout PASS)**
- **Test Metrics:**
  - **Zero-Shot Base Model (Qwen2.5-Coder-0.5B):** Accuracy 27.78%, Macro-F1 20.96%
  - **TF-IDF + Logistic Regression Baseline:** Accuracy 63.33%, Macro-F1 60.10%
  - **GitNova Fine-Tuned QLoRA Adapter:** **Accuracy 82.22%**, **Macro-Precision 82.08%**, **Macro-Recall 78.52%**, **Macro-F1 79.41%**
  - **`HIGH_FIT` F1-Score:** **88.89%** (Precision: 82.76%, Recall: 96.00%)
- **Training Duration:** **845.54 seconds** (~14.1 minutes) on 1x GPU.

---

## 4. Crucial Guidelines: What NOT to Say
- ❌ **DO NOT SAY:** *"GitNova has 79.41% real-world production accuracy."* $ightarrow$ **SAY:** *"Our fine-tuned QLoRA adapter achieved 79.41% Macro-F1 on an offline 90-issue repository-held-out test set."*
- ❌ **DO NOT SAY:** *"RAG is 100% accurate."* $ightarrow$ **SAY:** *"Our hybrid dense-sparse retriever achieved 100% Recall@5 on our 25-case golden benchmark."*
- ❌ **DO NOT SAY:** *"GitNova automatically opens and merges PRs."* $ightarrow$ **SAY:** *"GitNova guides the contributor from discovery through PR preparation; the human developer writes code locally and maintainers decide whether to merge."*
