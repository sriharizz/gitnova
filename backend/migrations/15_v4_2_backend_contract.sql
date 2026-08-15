-- Migration: 15_v4_2_backend_contract.sql
-- Description: Adds database fields to support precomputed issue explanations,
-- deterministic difficulty tiers, verification status, soft-delete issue lifecycle,
-- snapshot evaluation protection, and user preferences persistence.

-- 1. Extend issues table with lifecycle, verification, and precomputed explanation fields
ALTER TABLE issues
    ADD COLUMN IF NOT EXISTS github_state TEXT DEFAULT 'open' CHECK (github_state IN ('open', 'closed')),
    ADD COLUMN IF NOT EXISTS closed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS difficulty_score FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS difficulty_tier TEXT DEFAULT 'BEGINNER' CHECK (difficulty_tier IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')),
    ADD COLUMN IF NOT EXISTS domain_topics TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS estimated_time TEXT DEFAULT '~1-2 hours',
    ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'VERIFIED' CHECK (verification_status IN ('VERIFIED', 'NEEDS_REVIEW', 'INVALID')),
    ADD COLUMN IF NOT EXISTS verification_reasons TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS explanation JSONB DEFAULT NULL;

-- 2. Extend repository_snapshots to flag frozen evaluation ground-truth snapshots
ALTER TABLE repository_snapshots
    ADD COLUMN IF NOT EXISTS is_evaluation BOOLEAN DEFAULT FALSE;

-- 3. Create user_preferences table for optional preference storage
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT UNIQUE NOT NULL,
    preferred_languages TEXT[] DEFAULT '{}',
    preferred_domains TEXT[] DEFAULT '{}',
    preferred_difficulty TEXT CHECK (preferred_difficulty IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Create Indexes for fast filtering and ranking
CREATE INDEX IF NOT EXISTS idx_issues_difficulty_tier ON issues(difficulty_tier) WHERE is_published = TRUE;
CREATE INDEX IF NOT EXISTS idx_issues_verification_status ON issues(verification_status) WHERE is_published = TRUE;
CREATE INDEX IF NOT EXISTS idx_issues_domain_topics ON issues USING gin(domain_topics) WHERE is_published = TRUE;
CREATE INDEX IF NOT EXISTS idx_repository_snapshots_eval ON repository_snapshots(is_evaluation);
