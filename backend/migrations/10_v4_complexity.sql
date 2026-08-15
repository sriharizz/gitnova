-- Migration: 10_v4_complexity.sql
-- Description: Adds three columns to repos table to support the corrected
-- recommendation model where tier is derived from onboarding complexity,
-- not star count, and topics are stored for future interest-based filtering.
--
-- Rationale:
--   complexity_estimate: tier assignment now uses this instead of stars.
--   complexity_signals: stores the raw inputs for transparency/debugging.
--   topics: GitHub topics array, needed for future domain/interest matching.
--
-- IMPORTANT: complexity_estimate is PROVISIONAL in Sprint 3.
-- Sprint 5 will enhance it with file_count, total_loc, directory_depth
-- from cloned repository structure. The column stays — only the logic changes.

ALTER TABLE repos
    ADD COLUMN IF NOT EXISTS topics              TEXT[]  DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS complexity_estimate FLOAT   DEFAULT 50,
    ADD COLUMN IF NOT EXISTS complexity_signals  JSONB   DEFAULT '{}';

-- Index for future: filter by topic (interest matching)
CREATE INDEX IF NOT EXISTS idx_repos_topics
    ON repos USING gin(topics)
    WHERE is_active = TRUE;

-- Index for tier queries (now driven by complexity, not stars)
CREATE INDEX IF NOT EXISTS idx_repos_complexity
    ON repos(complexity_estimate)
    WHERE is_active = TRUE;
