-- Migration: 09_v4_pipeline_runs.sql
-- Description: Creates the pipeline_runs table for execution audit logging.
-- Every GitHub Actions worker run inserts a row here: start, end, counts, status.
-- This is how you answer "when did the pipeline last run?" in interviews.

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type          TEXT NOT NULL CHECK (run_type IN ('repo_qualification', 'issue_scan', 'code_index')),
    triggered_by      TEXT DEFAULT 'github_actions',  -- 'github_actions' | 'manual'
    started_at        TIMESTAMPTZ DEFAULT NOW(),
    finished_at       TIMESTAMPTZ,
    duration_seconds  INTEGER GENERATED ALWAYS AS (
                          EXTRACT(EPOCH FROM (finished_at - started_at))::INTEGER
                      ) STORED,
    repos_processed   INTEGER DEFAULT 0,
    items_found       INTEGER DEFAULT 0,
    items_published   INTEGER DEFAULT 0,
    status            TEXT DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed', 'partial')),
    error_log         TEXT,
    metadata          JSONB DEFAULT '{}'              -- any extra run-specific info
);

-- Fast lookup for monitoring: last N runs by type
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_type_started
    ON pipeline_runs(run_type, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
    ON pipeline_runs(status, started_at DESC);
