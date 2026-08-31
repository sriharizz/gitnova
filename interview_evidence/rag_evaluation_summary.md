# GitNova — Information Retrieval (RAG) Evaluation Evidence

**Ground-Truth Methodology:** Real historical developer pull requests from `fastapi/fastapi`, `pallets/click`, and `facebook/react` ([`backend/golden_set.csv`](file:///c:/gitNova/backend/golden_set.csv)).

---

## 1. Benchmarking Metrics

| Metric | Indexed Golden Benchmark (25 PRs) | Rolling CI/CD Benchmark (Unindexed Live Discovery) |
| :--- | :--- | :--- |
| **Recall@1** | **94.0%** | 1.1% (Limited by unindexed third-party repos) |
| **Recall@5** | **100.0%** | 3.9% |
| **Recall@10** | **100.0%** | 3.9% |
| **MRR@10** | **1.000** | **0.333** (MRR 1.000 on indexed cases like `open-headunit`) |
| **Hit@10** | **100.0%** | 33.3% |

---

## 2. Key Technical Formulations Implemented in Code
- **Deduplication**: File paths are deduplicated before computing Recall@K and MRR@K.
- **Hybrid Fusion**: Reciprocal Rank Fusion ($k=60$) combining dense cosine similarity and sparse PostgreSQL full-text search.
- **Information-Class Weighting**: Multiplier applied post-RRF ($1.10	imes$ for source code, $0.90	imes$ for tests).
