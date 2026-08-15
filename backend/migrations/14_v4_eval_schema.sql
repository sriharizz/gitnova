-- Migration: 14_v4_eval_schema.sql
-- Description: Extends existing eval_results table with GitNova v4.2 benchmark metrics.
-- Preserves existing columns (run_at, total_issues_evaluated, retrieval_recall, etc.)
-- Adds non-breaking default columns for Recall@10, Hit@10, MRR@10, CVR, HR, SAS, and Latency P50/P95.

ALTER TABLE eval_results
    ADD COLUMN IF NOT EXISTS dataset_version TEXT DEFAULT 'v4.2.0',
    ADD COLUMN IF NOT EXISTS eval_model TEXT DEFAULT 'openai/gpt-oss-120b',
    ADD COLUMN IF NOT EXISTS recall_at_10 FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS hit_at_10 FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS mrr_at_10 FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS citation_verification_rate FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS hallucination_rate FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS solution_actionability_score FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS latency_p50_ms INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS latency_p95_ms INTEGER DEFAULT 0;

COMMENT ON COLUMN eval_results.recall_at_10 IS 'Recall@10 metric across primary fix files';
COMMENT ON COLUMN eval_results.hit_at_10 IS 'Hit@10 metric across evaluation cases';
COMMENT ON COLUMN eval_results.mrr_at_10 IS 'Mean Reciprocal Rank (MRR@10) metric';
COMMENT ON COLUMN eval_results.citation_verification_rate IS 'Percentage of cited files/symbols verified in context';
COMMENT ON COLUMN eval_results.hallucination_rate IS 'Percentage of unverified/hallucinated file citations';
