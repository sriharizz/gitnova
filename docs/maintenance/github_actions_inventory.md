# GitNova — GitHub Actions Workflows Inventory

This document provides a comprehensive inventory of all automated workflows configured in `.github/workflows/`.

---

## 1. Workflows Summary Table

| Workflow File | Purpose | Trigger / Schedule | Script Executed | Dependencies / Secrets | Production Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [`daily_pipeline.yml`](file:///c:/gitNova/.github/workflows/daily_pipeline.yml) | Automated discovery, AST indexing, RAG retrieval, Gemini investigation, and publication | Cron: `0 6,18 * * *` (Twice daily at 6AM & 6PM UTC) + Manual Dispatch | `python -m app.pipeline.run_issue_sync` | `SUPABASE_URL`, `SUPABASE_KEY`, `GITHUB_TOKEN`, `GEMINI_API_KEY`, `JINA_API_KEY`, `GROQ_API_KEY` | **ACTIVE / CRITICAL PRODUCTION** |
| [`reindex.yml`](file:///c:/gitNova/.github/workflows/reindex.yml) | Full repository re-indexing and Tree-sitter AST chunk generation | Manual Workflow Dispatch | `python scripts/reindex_repos.py` | `SUPABASE_URL`, `SUPABASE_KEY`, `GITHUB_TOKEN`, `JINA_API_KEY` | **ACTIVE / MAINTENANCE TOOLING** |
| [`rolling_rag_eval.yml`](file:///c:/gitNova/.github/workflows/rolling_rag_eval.yml) | Automated longitudinal RAG benchmark against merged PR ground truth | Cron: `0 0 */3 * *` (Every 3 days at 00:00 UTC) + Manual Dispatch | `python -m app.pipeline.run_rolling_rag_eval` | `SUPABASE_URL`, `SUPABASE_KEY`, `GITHUB_TOKEN`, `JINA_API_KEY` | **ACTIVE / EVALUATION AUTOMATION** |

---

## 2. Dependency & Script Path Integrity
- `backend/app/pipeline/run_issue_sync.py`: Production entrypoint for scheduled discovery.
- `backend/scripts/reindex_repos.py`: Maintenance reindexer invoked by `reindex.yml`.
- `backend/app/pipeline/run_rolling_rag_eval.py`: Automated evaluator invoked by `rolling_rag_eval.yml`.

> [!NOTE]
> All GitHub Actions workflows reference valid paths. No workflows are obsolete or duplicate.
