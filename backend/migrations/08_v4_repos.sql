-- Migration: 08_v4_repos.sql
-- Description: Creates the repos table — the centerpiece of GitNova v4.2.
-- Every qualified repository lives here with its Contribution Success Score.
-- This is what the Repository Qualification Engine writes to every week.

CREATE TABLE IF NOT EXISTS repos (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name            TEXT NOT NULL UNIQUE,         -- e.g. "pallets/flask"
    stars                INTEGER DEFAULT 0,
    forks                INTEGER DEFAULT 0,
    language             TEXT,
    description          TEXT,
    license_spdx         TEXT,

    -- Contribution Success Score (0-100) + per-pillar breakdown
    score                FLOAT DEFAULT 0,
    score_grade          TEXT CHECK (score_grade IN ('excellent', 'good', 'fair', 'avoid')),
    score_breakdown      JSONB DEFAULT '{}',           -- {activity, beginner, responsiveness, documentation, health}
    score_explanation    JSONB DEFAULT '[]',           -- ["✓ Friendly maintainers", "⚠ Medium difficulty"]

    -- Tier: the user-facing journey level
    tier                 TEXT CHECK (tier IN ('starter', 'growing', 'established')),

    -- Lifecycle
    is_active            BOOLEAN DEFAULT TRUE,
    raw_metrics          JSONB DEFAULT '{}',           -- raw GitHub API data for debugging

    -- Timestamps
    first_discovered_at  TIMESTAMPTZ DEFAULT NOW(),
    last_scored_at       TIMESTAMPTZ,                  -- when the Qualification Engine last ran
    last_indexed_at      TIMESTAMPTZ,                  -- when code was last chunked + embedded
    updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Fast lookup for API: GET /repos?tier=starter&min_score=60
CREATE INDEX IF NOT EXISTS idx_repos_score
    ON repos(score DESC)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_repos_tier
    ON repos(tier)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_repos_language
    ON repos(language)
    WHERE is_active = TRUE;

-- Link issues to repos (issues table already exists from migration 01/03)
-- Add repo_id FK so we can join issues → repos for tier/score context
ALTER TABLE issues
    ADD COLUMN IF NOT EXISTS repo_id UUID REFERENCES repos(id),
    ADD COLUMN IF NOT EXISTS competition_level TEXT CHECK (competition_level IN ('low', 'medium', 'high')),
    ADD COLUMN IF NOT EXISTS freshness_label TEXT,     -- "Updated 3 days ago"
    ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE;

-- Index for API: GET /issues?tier=starter&quality=high
CREATE INDEX IF NOT EXISTS idx_issues_published
    ON issues(is_published, quality_score DESC)
    WHERE is_published = TRUE;

