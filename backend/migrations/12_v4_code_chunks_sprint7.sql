-- Migration: 12_v4_code_chunks_sprint7.sql
-- Description: Extends code_chunks table with Sprint 6 metadata fields and repo_id foreign key link.
--
-- Preserves existing table, vector(768) column, and indexes.
-- Adds info_class, qualified_symbol_name, symbol_type, parent_symbol, contextual_header, parser_strategy, and repo_id.

ALTER TABLE code_chunks
    ADD COLUMN IF NOT EXISTS repo_id UUID REFERENCES repos(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS info_class TEXT,
    ADD COLUMN IF NOT EXISTS qualified_symbol_name TEXT,
    ADD COLUMN IF NOT EXISTS symbol_type TEXT,
    ADD COLUMN IF NOT EXISTS parent_symbol TEXT,
    ADD COLUMN IF NOT EXISTS contextual_header TEXT,
    ADD COLUMN IF NOT EXISTS parser_strategy TEXT;

-- Index repo_id for fast lookup
CREATE INDEX IF NOT EXISTS idx_code_chunks_repo_id
    ON code_chunks(repo_id);

-- Index info_class for filtering by document/source/config type
CREATE INDEX IF NOT EXISTS idx_code_chunks_info_class
    ON code_chunks(info_class);

COMMENT ON COLUMN code_chunks.info_class IS 'DOCUMENTATION | SOURCE_CODE | CONFIGURATION | TESTS';
COMMENT ON COLUMN code_chunks.contextual_header IS 'Deterministic header string (e.g. [File: ... | Class: ...]) embedded alongside code content';
