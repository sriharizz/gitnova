# GitNova — Proposed Repository Structure & Cleanup Plan

This document outlines the professional target directory organization for the GitNova repository.

---

## 1. Target Directory Organization

```
gitnova/
├── .github/
│   └── workflows/
│       ├── daily_pipeline.yml            # Automated discovery & ingestion cron
│       ├── reindex.yml                   # Repository AST reindexer
│       └── rolling_rag_eval.yml          # Automated 3-day rolling RAG benchmark
├── backend/
│   ├── app/                              # PRODUCTION APPLICATION CORE (STRICTLY LOCKED)
│   │   ├── api/                          # FastAPI route handlers
│   │   ├── core/                         # Configuration & logging
│   │   ├── db/                           # Supabase PostgreSQL client & models
│   │   ├── evaluation/                   # Core metric calculations (Recall@K, MRR, Hit@K)
│   │   ├── pipeline/                     # Discovery, Filtering, Tree-sitter, RAG, Gemini
│   │   └── schemas/                      # Pydantic schemas (IssueExplanation, Journey)
│   ├── data/                             # PERSISTED DATASETS & ML EXPERIMENTS
│   │   ├── dataset_collection/           # Reproducible QLoRA dataset & adapter model
│   │   ├── qlora_shadow_demo/            # READ-ONLY shadow evaluation predictions & report
│   │   └── rolling_rag_eval_*            # Longitudinal RAG benchmark datasets & audits
│   ├── migrations/                       # Ordered PostgreSQL SQL migrations (01 to 16)
│   ├── scripts/                          # SYSTEM ENGINEERING & EXPERIMENT TOOLING
│   │   ├── analysis/                     # Diagnostic audits, deep-dive forensic scripts, inspect
│   │   ├── dataset/                      # Fine-tuning dataset preparation & QLoRA training
│   │   ├── evaluation/                   # Benchmark runners (longitudinal, golden, batch eval)
│   │   └── maintenance/                  # Database migration verifiers, reindexing, seeding
│   ├── tests/                            # Unit and integration test suites
│   ├── requirements.txt                  # Python production dependencies
│   └── Dockerfile                        # Backend container specification
├── frontend/                             # PRODUCTION REACT 19 + VITE FRONTEND
│   ├── src/                              # Components, pages, hooks, state, types
│   ├── package.json                      # Node dependencies
│   ├── vite.config.ts                    # Vite build configuration
│   └── vercel.json                       # Vercel deployment configuration
├── docs/                                 # SYSTEM DOCUMENTATION & ARCHITECTURE
│   ├── architecture/                     # System design, data flow, hybrid RAG diagrams
│   ├── evaluation/                       # Metric formulations & benchmark reports
│   └── maintenance/                      # Inventory, cleanup audit, post-maintenance reports
├── interview_evidence/                   # STRUCTURED INTERVIEW DEMONSTRATION SUITE
│   ├── context/                          # 121 individual issue context packs
│   ├── traces/                           # Full end-to-end execution traces
│   ├── frontend_issue_audit/             # 10-stage audited frontend demo issues
│   ├── GITNOVA_INTERVIEW_TECHNICAL_STORY.md
│   ├── VERIFIED_INTERVIEW_NUMBERS.md
│   ├── FINAL_DEMO_PLAN.md
│   └── INTERVIEW_RUNBOOK.md
├── README.md                             # Primary repository README & quickstart
└── LICENSE                               # MIT License
```

---

## 2. Script Organization Mapping Table

| Original Script Path | New Organized Path | Functional Category | Rationale |
| :--- | :--- | :--- | :--- |
| `backend/scripts/run_longitudinal_evaluation.py` | `backend/scripts/evaluation/run_longitudinal_evaluation.py` | Evaluation | Longitudinal RAG benchmark runner |
| `backend/scripts/run_10_eval_batch.py` | `backend/scripts/evaluation/run_10_eval_batch.py` | Evaluation | 10-issue evaluation batch runner |
| `backend/scripts/evaluate_gitnova_model.py` | `backend/scripts/evaluation/evaluate_gitnova_model.py` | Evaluation | Candidate model evaluator |
| `backend/scripts/evaluate_v4_5_final_8repos.py` | `backend/scripts/evaluation/evaluate_v4_5_final_8repos.py` | Evaluation | 8-repo validation evaluator |
| `backend/scripts/evaluate_v4_5_quality.py` | `backend/scripts/evaluation/evaluate_v4_5_quality.py` | Evaluation | Quality gate evaluator |
| `backend/scripts/measure_llm_reliability.py` | `backend/scripts/evaluation/measure_llm_reliability.py` | Evaluation | Gemini reliability & latency benchmark |
| `backend/scripts/run_v4_5_three_issues_quality_gate.py` | `backend/scripts/evaluation/run_v4_5_three_issues_quality_gate.py` | Evaluation | 3-issue quality gate runner |
| `backend/scripts/collect_finetuning_dataset.py` | `backend/scripts/dataset/collect_finetuning_dataset.py` | Dataset | Ingestion & annotation collector |
| `backend/scripts/run_gitnova_qlora_experiment.py` | `backend/scripts/dataset/run_gitnova_qlora_experiment.py` | Dataset | QLoRA training & test evaluation |
| `backend/scripts/reindex_repos.py` | `backend/scripts/maintenance/reindex_repos.py` | Maintenance | AST re-indexer (delegated shim kept at root) |
| `backend/scripts/clean_database_v2.py` | `backend/scripts/maintenance/clean_database_v2.py` | Maintenance | Database maintenance tool |
| `backend/scripts/clean_supabase.py` | `backend/scripts/maintenance/clean_supabase.py` | Maintenance | Database cleanup utility |
| `backend/scripts/export_supabase.py` | `backend/scripts/maintenance/export_supabase.py` | Maintenance | Data backup & export tool |
| `backend/scripts/run_canonical_pilot_ingestion.py` | `backend/scripts/maintenance/run_canonical_pilot_ingestion.py` | Maintenance | Pilot ingestion runner |
| `backend/scripts/run_canonical_real_issue_trace.py` | `backend/scripts/maintenance/run_canonical_real_issue_trace.py` | Maintenance | Canonical trace runner |
| `backend/scripts/run_final_pre_deployment_validation.py` | `backend/scripts/maintenance/run_final_pre_deployment_validation.py` | Maintenance | Deployment validation suite |
| `backend/scripts/run_single_issue_ingestion.py` | `backend/scripts/maintenance/run_single_issue_ingestion.py` | Maintenance | Single issue ingestion tool |
| `backend/scripts/seed_live_published_issues.py` | `backend/scripts/maintenance/seed_live_published_issues.py` | Maintenance | Database seeder |
| `backend/scripts/verify_index_coverage_regression.py` | `backend/scripts/maintenance/verify_index_coverage_regression.py` | Maintenance | Index coverage verification |
| `backend/scripts/verify_post_migration_16.py` | `backend/scripts/maintenance/verify_post_migration_16.py` | Maintenance | Migration 16 verifier |
| `backend/scripts/verify_production_pipeline_dry_run.py` | `backend/scripts/maintenance/verify_production_pipeline_dry_run.py` | Maintenance | Pipeline dry-run verifier |
| `backend/scripts/analyze_diagnostic_results.py` | `backend/scripts/analysis/analyze_diagnostic_results.py` | Analysis | Diagnostic result analyzer |
| `backend/scripts/analyze_longitudinal_buckets.py` | `backend/scripts/analysis/analyze_longitudinal_buckets.py` | Analysis | Longitudinal bucket classifier |
| `backend/scripts/audit_9_grounding_failures.py` | `backend/scripts/analysis/audit_9_grounding_failures.py` | Analysis | Grounding failure auditor |
| `backend/scripts/audit_and_expand_real_issues.py` | `backend/scripts/analysis/audit_and_expand_real_issues.py` | Analysis | Issue auditor |
| `backend/scripts/audit_bucket_a_deep_dive.py` | `backend/scripts/analysis/audit_bucket_a_deep_dive.py` | Analysis | Bucket A deep-dive auditor |
| `backend/scripts/audit_evaluation_model.py` | `backend/scripts/analysis/audit_evaluation_model.py` | Analysis | Diagnostic model auditor |
| `backend/scripts/audit_frontend_demo_issues.py` | `backend/scripts/analysis/audit_frontend_demo_issues.py` | Analysis | Frontend demo issue auditor |
| `backend/scripts/build_interview_evidence_pack.py` | `backend/scripts/analysis/build_interview_evidence_pack.py` | Analysis | Evidence pack builder |
| `backend/scripts/export_issues_dossier.py` | `backend/scripts/analysis/export_issues_dossier.py` | Analysis | Dossier exporter |
| `backend/scripts/extract_10_audit_cases.py` | `backend/scripts/analysis/extract_10_audit_cases.py` | Analysis | Case extractor |
| `backend/scripts/extract_log_snippets.py` | `backend/scripts/analysis/extract_log_snippets.py` | Analysis | Log snippet extractor |
| `backend/scripts/finalize_bucket_a_audit.py` | `backend/scripts/analysis/finalize_bucket_a_audit.py` | Analysis | Bucket A audit report builder |
| `backend/scripts/finalize_trace_from_jsonl.py` | `backend/scripts/analysis/finalize_trace_from_jsonl.py` | Analysis | Trace builder |
| `backend/scripts/find_3_new_real_issues.py` | `backend/scripts/analysis/find_3_new_real_issues.py` | Analysis | Real issue finder |
| `backend/scripts/generate_full_10_issue_report.py` | `backend/scripts/analysis/generate_full_10_issue_report.py` | Analysis | 10-issue report generator |
| `backend/scripts/generate_interview_master_artifacts.py` | `backend/scripts/analysis/generate_interview_master_artifacts.py` | Analysis | Master artifact builder |
| `backend/scripts/inspect_longitudinal_hits.py` | `backend/scripts/analysis/inspect_longitudinal_hits.py` | Analysis | Longitudinal hit inspector |
| `backend/scripts/inspect_rotation.py` | `backend/scripts/analysis/inspect_rotation.py` | Analysis | Ingestion rotation inspector |
| `backend/scripts/prepare_audit_update.py` | `backend/scripts/analysis/prepare_audit_update.py` | Analysis | Audit updater |
| `backend/scripts/run_diagnostic_40_experiment.py` | `backend/scripts/analysis/run_diagnostic_40_experiment.py` | Analysis | Diagnostic experiment runner |
| `backend/scripts/verify_trace_csv.py` | `backend/scripts/analysis/verify_trace_csv.py` | Analysis | Trace CSV verifier |

---

## 3. Backward Compatibility & Root Shims
To guarantee that existing workflows (such as `.github/workflows/reindex.yml`) and standard commands continue to function without disruption, a lightweight backward-compatible shim is maintained at `backend/scripts/reindex_repos.py` pointing to `backend/scripts/maintenance/reindex_repos.py`.
"""

with open(docs_maint / "proposed_repository_structure.md", "w", encoding="utf-8") as f:
    f.write(CodeContent)
