-- Migration: 13_v4_hybrid_search_sprint8.sql
-- Description: Hardened RPC functions match_chunks_vector and match_chunks_lexical:
--   1. Strict Repository Isolation Guard: Raises exception if both target_repo_id and target_repo are NULL.
--   2. Strict Snapshot Isolation: Joins with repository_snapshots and filters status = 'ACTIVE' ONLY.
--   3. Security Hardening: Sets explicit search_path = public, extensions on SECURITY DEFINER.
--   4. Returns Sprint 6/7 metadata fields (repo_id, info_class, qualified_symbol_name, symbol_type, contextual_header).

-- 1. Vector similarity search function (v4 hardened)
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
  -- Strict Repository Isolation Guard: Never allow unbounded cross-repository queries
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

-- 2. Lexical (keyword) search function (v4 hardened)
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
  -- Strict Repository Isolation Guard: Never allow unbounded cross-repository queries
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
