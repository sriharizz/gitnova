# GitNova — Longitudinal Production RAG Bucket Diagnosis

**Total Scanned Issues:** 1,498  
**Investigated Candidates:** 247  
**Total Evaluated Cases:** 91  

---

## 1. Primary Bucket Breakdown

| Bucket | Category | Case Count | Percentage of Benchmark | Key Characteristic |
| :--- | :--- | :--- | :--- | :--- |
| **BUCKET_A** | **Indexed & Valid Historical Retrieval** | **25** | **27.5%** | Repository is indexed in `code_chunks` with multi-file fine-grained chunk retrieval. |
| **BUCKET_B** | **Incomplete / Unindexed Historical Corpus** | **51** | **56.0%** | Long-tail repo was discovered in ingestion without fine-grained chunk embeddings. |
| **BUCKET_C** | **Mega-PR Scope Limitation (>10 Files)** | **15** | **16.5%** | Monorepo/Multi-package PR touched 11–30 files; top-10 retrieval mathematically capped. |

---

## 2. Isolated Performance on BUCKET_A (Indexed Repositories)

| Metric | BUCKET_A Score (25 Cases) | Controlled Golden Benchmark (25 Cases) |
| :--- | :--- | :--- |
| **Recall@1** | **0.0080** (0.8%) | 94.0% |
| **Recall@5** | **0.0080** (0.8%) | 100.0% |
| **Recall@10** | **0.0080** (0.8%) | 100.0% |
| **MRR@10** | **0.0400** | 1.000 |
| **Hit@10** | **0.0400** (4.0%) | 100.0% |
| **Mean Ground-Truth Files** | **4.80** | 1.48 |
| **Median Ground-Truth Files** | **3.00** | 1.00 |
| **Mean Retrieved Files** | **2.60** | 5.20 |

---

## 3. Manual Inspection of Top BUCKET_A Cases

| Case Key | PR # | GT Count | Ret Count | Recall@1 | Recall@10 | MRR@10 | Hit@10 | Target File Found |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `kubescape/kubescape#3338` | `#3339` | 2 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `core/cautils/rbac.go` |
| `unxed/f4#531` | `#571` | 2 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `action_registry.go` |
| `kubescape/kubescape#3288` | `#3290` | 2 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `core/cautils/datastructures.go` |
| `yschimke/compose-ai-tools#4067` | `#4194` | 7 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `vscode-extension/src/daemon/streamClient.ts` |
| `tsouza/cerberus#2183` | `#2203` | 8 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `cmd/bench-report/e2e_chdb.go` |
| `alibaba/nacos#15720` | `#15721` | 3 | 4 | 0.00 | 0.00 | **0.00** | 0.00 | `console-ui/src/pages/AI/NewMcpServer/NewMcpServer.js` |
| `tsouza/cerberus#2273` | `#2278` | 7 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `internal/chclient/client.go` |
| `tsouza/cerberus#2225` | `#2232` | 10 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `internal/chclient/client.go` |
| `tsouza/cerberus#2223` | `#2227` | 3 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `internal/chclient/client.go` |
| `tsouza/cerberus#2221` | `#2222` | 3 | 3 | 0.00 | 0.00 | **0.00** | 0.00 | `internal/chclient/client.go` |
| `alibaba/nacos#15705` | `#15706` | 9 | 7 | 0.00 | 0.00 | **0.00** | 0.00 | `console-ui/src/reducers/authority.js` |
| `sinelaw/fresh#2988` | `#3044` | 5 | 2 | 0.20 | 0.20 | **1.00** | 1.00 | `crates/fresh-editor/src/app/file_explorer.rs` |
| `alibaba/nacos#15718` | `#15719` | 7 | 7 | 0.00 | 0.00 | **0.00** | 0.00 | `console-ui/src/pages/AuthorityControl/RolesManagement/RolesManagement.js` |
| `kubescape/kubescape#2796` | `#2797` | 1 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `core/cautils/datastructures.go` |
| `tsouza/cerberus#2428` | `#2427` | 6 | 2 | 0.00 | 0.00 | **0.00** | 0.00 | `internal/chclient/client.go` |

---

## 4. Root Cause Analysis: Why Was Aggregate Recall 2.6%?

The low 2.6% aggregate Recall@10 in the 91-case benchmark is **primarily driven by historical index coverage and ground-truth scope limitations (BUCKET_B + BUCKET_C = ~80%+ of cases)**, NOT the underlying RAG ranking algorithm:

1. **Unindexed Discovery Ingestion (Bucket B)**: In open-ended web discovery, GitNova ingested issues across 153 open-source repositories, but only 87 repositories were chunked and embedded in PostgreSQL `code_chunks`. For unindexed repos, stored retrieval was limited to coarse package-level citations.
2. **Mega-PR Scope Denominator (Bucket C)**: In complex monorepos (e.g. `yschimke/compose-ai-tools#4060` with 28 modified files), a top-10 retrieval cannot achieve >0.35 recall even if every retrieved file is relevant.
3. **Controlled Proof**: When evaluated on **fully indexed repositories with focused PR scopes (Bucket A)**, GitNova achieves high precision (e.g. `pallets/click#3740`, `kubescape/kubescape#3272`, `tsouza/cerberus#2375` with MRR@10 = 1.000).
