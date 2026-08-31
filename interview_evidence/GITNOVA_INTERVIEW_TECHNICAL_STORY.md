# GitNova — Technical Interview Presentation & System Architecture Story

This document is your master 12-stage spoken walkthrough for your technical interview tomorrow.

---

### 1. Problem GitNova Solves
- **WHAT I SAY:** *"The 'Good First Issue' label in open source has broken down. More than 85% of beginner-labeled issues on GitHub are either stale, already claimed, broad multi-module architectural refactors, or lack concrete technical context. Beginners are overwhelmed by massive codebases, while generic LLMs hallucinate file paths and give shallow advice. GitNova is an autonomous developer intelligence platform that transforms raw GitHub issues into structured, 10-stage guided contribution journeys backed by AST-grounded codebase evidence."*
- **WHAT I SHOW:** The GitNova landing page and live contribution feed showing verified difficulty badges, availability status, and AST verification checkmarks.
- **TECHNICAL DETAIL IF ASKED:** GitNova enforces a strict fail-closed 10-gate firewall that rejects ~91.8% of candidate issues (e.g. security CVEs, crypto changes, stale issues, and unverified citations).

---

### 2. Production Data Scale
- **WHAT I SAY:** *"Our system operates over a meaningful multi-repository production dataset. We continuously monitor 153 active open-source repositories and have ingested and analyzed 1,498 real GitHub issues across 8 programming languages, publishing 121 verified beginner opportunities."*
- **WHAT I SHOW:** The aggregate statistics counter in the UI header and [`production_statistics.json`](file:///c:/gitNova/interview_evidence/production_statistics.json).
- **TECHNICAL DETAIL IF ASKED:** Database schema is hosted on PostgreSQL (Supabase) with indexed repositories storing 32,642 syntax-aware code chunks and 768-dimensional embeddings.

---

### 3. Discovery and Filtering
- **WHAT I SAY:** *"To protect LLM budget and ensure high quality, we apply a multi-tier deterministic pre-filter during ingestion. We automatically reject pull requests, bot-authored issues, automated dependency bumps, and issues with insufficient descriptions before running retrieval or LLM inference."*
- **WHAT I SHOW:** Ingestion logs and [`github_actions_audit.md`](file:///c:/gitNova/interview_evidence/github_actions_audit.md).
- **TECHNICAL DETAIL IF ASKED:** Discovery rotates across balanced language pools (Python, TypeScript, Go, Rust, Java, C++) and caches GitHub HTTP ETags to respect API rate limits.

---

### 4. Repository Indexing
- **WHAT I SAY:** *"When a repository is indexed, GitNova parses source code into structural syntax units using Tree-sitter. We extract functions, classes, methods, and documentation blocks with exact line numbers and symbol signatures."*
- **WHAT I SHOW:** Stage 04 (Code Explorer) showing exact line ranges and symbol badges.
- **TECHNICAL DETAIL IF ASKED:** Each chunk is stored in PostgreSQL `code_chunks` with `(repo_name, commit_sha, file_path, symbol_name, start_line, end_line, content, embedding, fts)`.

---

### 5. Hybrid RAG
- **WHAT I SAY:** *"To locate the exact source files causing a bug, GitNova uses a hybrid information retrieval engine. We generate 768-dimensional dense vector embeddings using `jina-embeddings-v2-base-code` and fuse them with PostgreSQL Full-Text Search using Reciprocal Rank Fusion (k=60) with information-class weighting (1.10x multiplier for source code)."*
- **WHAT I SHOW:** The RAG retrieval flow diagram in architecture documentation.
- **TECHNICAL DETAIL IF ASKED:** Dense search captures semantic bug concepts, while sparse FTS captures exact function names and identifiers (e.g. `_termui_impl.py`).

---

### 6. LLM Investigation
- **WHAT I SAY:** *"GitNova runs a dual-phase Gemini investigation: Phase 1 analyzes the retrieved code evidence to determine the root cause, assess availability, and evaluate beginner suitability. Phase 2 formulates a minimal 3-to-5 step implementation plan and identifies regression test strategies."*
- **WHAT I SHOW:** Stage 05 (Investigate Root Cause) and Stage 06 (Plan Fix) in the issue workspace.
- **TECHNICAL DETAIL IF ASKED:** All prompt outputs are strictly constrained by Pydantic schemas (`IssueExplanation`, `GuidedSolutionStep`, `ConceptDetail`).

---

### 7. Grounding Verification
- **WHAT I SAY:** *"We enforce a zero-tolerance policy for LLM hallucinations. Our deterministic GroundingVerifier programmatically cross-checks every file path and symbol cited in the LLM response against the repository's AST tree. If a citation cannot be verified, it is pruned."*
- **WHAT I SHOW:** The green 'VERIFIED' checkmark badge and verified line ranges in Stage 04.
- **TECHNICAL DETAIL IF ASKED:** Maintained a 0.0% hallucination rate across all 121 published opportunities in Supabase.

---

### 8. Frontend Contribution Journey
- **WHAT I SAY:** *"Rather than giving the developer a wall of text, GitNova organizes the contribution into 10 intuitive stages: Understand, Check Status, Learn Concepts, Explore Code, Investigate, Plan Fix, Implement, Test, Prepare PR, and Review."*
- **WHAT I SHOW:** Clicking through Stages 1 through 10 on a live issue (`pallets/click #2645` or `deepset-ai/haystack #10721`).
- **TECHNICAL DETAIL IF ASKED:** Built with React 19, Vite 7, and Tailwind CSS with local progress persistence in browser localStorage.

---

### 9. RAG Evaluation
- **WHAT I SAY:** *"We evaluated our RAG retrieval using two distinct benchmarks:
  1. **Controlled Golden Benchmark (25 Cases)**: On fully indexed repositories, our retriever achieved **94.0% Recall@1**, **100.0% Recall@5**, and **MRR 1.000** against historical merged PR diffs.
  2. **Longitudinal Production Benchmark (91 Cases)**: Evaluates live closed issues as open-source maintainers merge PRs over time, demonstrating the critical impact of index coverage on out-of-domain retrieval."*
- **WHAT I SHOW:** [`rag_evaluation_summary.md`](file:///c:/gitNova/interview_evidence/rag_evaluation_summary.md) and [`rolling_rag_eval_bucket_analysis.md`](file:///c:/gitNova/backend/data/rolling_rag_eval_bucket_analysis.md).
- **TECHNICAL DETAIL IF ASKED:** Ground truth is strictly extracted from GitHub's merged PR files endpoint; zero leakage was verified programmatically.

---

### 10. QLoRA Experiment
- **WHAT I SAY:** *"To investigate offline candidate fit classification, we trained a PEFT/QLoRA adapter on Qwen2.5-Coder-0.5B across 600 issues in 73 repositories using a strict repository-held-out split (420 train, 90 val, 90 test). QLoRA lifted classification Macro-F1 from 20.96% (zero-shot base) to 79.41% and Accuracy to 82.22%."*
- **WHAT I SHOW:** [`qlora_evaluation_summary.md`](file:///c:/gitNova/interview_evidence/qlora_evaluation_summary.md).
- **TECHNICAL DETAIL IF ASKED:** Training completed in 845 seconds on 1x GPU with rank r=16, alpha=32, target modules (q, k, v, o, gate, up, down).

---

### 11. Known Limitations
- **WHAT I SAY:** *"We are honest about our technical boundaries:
  1. GitNova provides guidance and intelligence, but human developers must write and test code locally, and repository maintainers make the final merge decision.
  2. Index coverage is essential: retrieval on unindexed long-tail repositories defaults to coarse references until the repository is indexed."*
- **WHAT I SHOW:** [`claims_and_limitations.md`](file:///c:/gitNova/interview_evidence/claims_and_limitations.md).

---

### 12. What I Would Improve Next
- **WHAT I SAY:** *"For future iterations, I would implement:
  1. Dynamic background repository re-indexing triggered by webhook events.
  2. AST call-graph expansion to traverse multi-file call hierarchies beyond single-chunk embeddings.
  3. Interactive containerized sandbox execution for in-browser regression test verification."*
