-- Migration: 16_v4_rpc_deduplication.sql
-- Description: 
--   1. Drops obsolete overloaded 4-parameter RPC functions to eliminate PGRST203 PostgREST ambiguity.
--   2. Standardizes on a single canonical 5-parameter version of match_chunks_vector and match_chunks_lexical.
--   3. Applies remaining schema contracts (user_preferences table, eval_results columns, issues lifecycle fields).

-- 1. Drop obsolete 4-parameter overloaded functions
DROP FUNCTION IF EXISTS match_chunks_vector(vector(768), text, text, integer);
DROP FUNCTION IF EXISTS match_chunks_lexical(text, text, text, integer);

-- 2. Create single canonical 5-parameter Vector Search RPC
CREATE OR REPLACE FUNCTION match_chunks_vector(
  query_embedding vector(768),
  target_repo text DEFAULT NULL,
  target_commit text DEFAULT NULL,
  match_count int DEFAULT 20,
  target_repo_id uuid DEFAULT NULL
)
RETURNS TABLE (
  chunk_id text,
  file_path text,
  symbol_name text,
  start_line integer,
  end_line integer,
  content text,
  similarity float,
  repo_id uuid,
  info_class text,
  qualified_symbol_name text,
  symbol_type text,
  contextual_header text
)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, extensions AS $$
BEGIN
  -- Repository Isolation Guard: Ensure queries are bounded to a repo
  IF target_repo_id IS NULL AND (target_repo IS NULL OR trim(target_repo) = '') THEN
    RAISE EXCEPTION 'Repository isolation error: Either target_repo_id or target_repo MUST be provided.';
  END IF;

  RETURN QUERY
  SELECT
    cc.chunk_id,
    cc.file_path,
    cc.symbol_name,
    cc.start_line,
    cc.end_line,
    cc.content,
    (1 - (cc.embedding <=> query_embedding))::float AS similarity,
    cc.repo_id,
    cc.info_class,
    cc.qualified_symbol_name,
    cc.symbol_type,
    cc.contextual_header
  FROM code_chunks cc
  JOIN repository_snapshots rs ON cc.snapshot_id = rs.id
  WHERE rs.status = 'ACTIVE'
    AND (target_repo_id IS NULL OR cc.repo_id = target_repo_id)
    AND (target_repo IS NULL OR cc.repo_name = target_repo)
    AND (target_commit IS NULL OR cc.commit_sha = target_commit)
  ORDER BY cc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 3. Create single canonical 5-parameter Lexical Search RPC
CREATE OR REPLACE FUNCTION match_chunks_lexical(
  query_text text,
  target_repo text DEFAULT NULL,
  target_commit text DEFAULT NULL,
  match_count int DEFAULT 20,
  target_repo_id uuid DEFAULT NULL
)
RETURNS TABLE (
  chunk_id text,
  file_path text,
  symbol_name text,
  start_line integer,
  end_line integer,
  content text,
  lexical_rank float,
  repo_id uuid,
  info_class text,
  qualified_symbol_name text,
  symbol_type text,
  contextual_header text
)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, extensions AS $$
BEGIN
  -- Repository Isolation Guard: Ensure queries are bounded to a repo
  IF target_repo_id IS NULL AND (target_repo IS NULL OR trim(target_repo) = '') THEN
    RAISE EXCEPTION 'Repository isolation error: Either target_repo_id or target_repo MUST be provided.';
  END IF;

  RETURN QUERY
  SELECT
    cc.chunk_id,
    cc.file_path,
    cc.symbol_name,
    cc.start_line,
    cc.end_line,
    cc.content,
    ts_rank_cd(cc.fts, plainto_tsquery('simple', query_text))::float AS lexical_rank,
    cc.repo_id,
    cc.info_class,
    cc.qualified_symbol_name,
    cc.symbol_type,
    cc.contextual_header
  FROM code_chunks cc
  JOIN repository_snapshots rs ON cc.snapshot_id = rs.id
  WHERE rs.status = 'ACTIVE'
    AND (target_repo_id IS NULL OR cc.repo_id = target_repo_id)
    AND (target_repo IS NULL OR cc.repo_name = target_repo)
    AND (target_commit IS NULL OR cc.commit_sha = target_commit)
    AND cc.fts @@ plainto_tsquery('simple', query_text)
  ORDER BY lexical_rank DESC
  LIMIT match_count;
END;
$$;

-- 4. Apply non-breaking columns to issues table
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

-- 5. Extend repository_snapshots for evaluation flags
ALTER TABLE repository_snapshots
    ADD COLUMN IF NOT EXISTS is_evaluation BOOLEAN DEFAULT FALSE;

-- 6. Apply user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT UNIQUE NOT NULL,
    preferred_languages TEXT[] DEFAULT '{}',
    preferred_domains TEXT[] DEFAULT '{}',
    preferred_difficulty TEXT CHECK (preferred_difficulty IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Extend eval_results table
ALTER TABLE eval_results
    ADD COLUMN IF NOT EXISTS dataset_version TEXT DEFAULT 'v4.2.0',
    ADD COLUMN IF NOT EXISTS eval_model TEXT DEFAULT 'gemini-3.6-flash',
    ADD COLUMN IF NOT EXISTS recall_at_10 FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS hit_at_10 FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS mrr_at_10 FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS citation_verification_rate FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS hallucination_rate FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS solution_actionability_score FLOAT DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS latency_p50_ms INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS latency_p95_ms INTEGER DEFAULT 0;
