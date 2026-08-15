-- Migration: 11_v4_unavailable_metrics.sql
-- Description: Adds unavailable_metrics column to repos table.
--
-- This column records which GitHub API sub-requests failed during collection,
-- making the corresponding score components conservative (0 instead of observed value).
-- It is surfaced in the API response so consumers can see the confidence level.
--
-- Example: ["pull_requests_30d", "contributor_count"]
-- An empty array means all metrics were successfully collected.

ALTER TABLE repos
    ADD COLUMN IF NOT EXISTS unavailable_metrics TEXT[] DEFAULT '{}';

COMMENT ON COLUMN repos.unavailable_metrics IS
    'GitHub API sub-requests that failed during collection. '
    'Corresponding score components are conservatively scored as 0. '
    'Empty array = all metrics successfully collected.';
