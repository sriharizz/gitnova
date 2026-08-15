"""
GitNova v4.2 — Sprint 7 Vector Indexer Unit & Policy Tests

Tests for:
  - IndexingPolicy eligibility and storage budget enforcement
  - Incremental SHA-based indexing checks (is_repo_indexing_required)
  - Text payload preparation for 768-dim embedding (contextual_header + raw_content)
  - Embedding batch shape (768 dimensions per chunk)
  - Snapshot lifecycle & atomic activation (STAGING -> ACTIVE)
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
import pytest

from app.intelligence.chunker import CodeChunk, ChunkedRepository
from app.intelligence.pipeline_vector_index import (
    VectorIndexConfig,
    IndexingPolicy,
    prepare_text_for_embedding,
    index_qualified_repository,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_sample_code_chunk(
    chunk_id: str = "chunk_001",
    file_path: str = "src/app.py",
    symbol_name: str = "main",
    qualified_symbol_name: str = "main",
    symbol_type: str = "function",
    raw_content: str = "def main():\n    return 42\n",
) -> CodeChunk:
    return CodeChunk(
        chunk_id=chunk_id,
        file_path=file_path,
        language="Python",
        info_class="SOURCE_CODE",
        symbol_name=symbol_name,
        qualified_symbol_name=qualified_symbol_name,
        symbol_type=symbol_type,
        parent_symbol=None,
        start_line=1,
        end_line=2,
        raw_content=raw_content,
        contextual_header=f"[File: {file_path} | Function: {symbol_name} (Lines 1-2)]",
        token_estimate=5,
        parser_strategy="python_ast",
    )


def make_sample_chunked_repo(chunks: list = None) -> ChunkedRepository:
    chunks = chunks or [make_sample_code_chunk()]
    return ChunkedRepository(
        full_name="pallets/flask",
        total_chunks=len(chunks),
        total_tokens=sum(c.token_estimate for c in chunks),
        total_bytes=sum(len(c.raw_content) for c in chunks),
        corpus_files_available=1,
        files_processed=1,
        files_skipped_budget=0,
        chunks_by_info_class={"SOURCE_CODE": len(chunks)},
        chunks_by_parser_strategy={"python_ast": len(chunks)},
        min_chunk_tokens=5,
        avg_chunk_tokens=5.0,
        max_chunk_tokens=5,
        parser_fallbacks_occurred=False,
        chunks=chunks,
    )


# ── Text Payload Preparation Tests ────────────────────────────────────────────

class TestTextPayloadPreparation:

    def test_combines_header_and_raw_content(self):
        chunk = make_sample_code_chunk(
            file_path="src/auth.py",
            symbol_name="authenticate",
            raw_content="def authenticate():\n    return True\n",
        )
        payload = prepare_text_for_embedding(chunk)
        assert payload.startswith("[File: src/auth.py")
        assert "def authenticate():" in payload

    def test_payload_length_capped_at_4000(self):
        long_content = "x = 1\n" * 2000
        chunk = make_sample_code_chunk(raw_content=long_content)
        payload = prepare_text_for_embedding(chunk)
        assert len(payload) <= 4000


# ── Indexing Policy & Incremental Check Tests ─────────────────────────────────

class TestIndexingPolicy:

    @pytest.mark.anyio
    async def test_is_repo_indexing_required_returns_false_if_sha_matches(self):
        policy = IndexingPolicy()

        conn_mock = AsyncMock()
        conn_mock.fetchrow = AsyncMock(return_value={"id": UUID("00000000-0000-0000-0000-000000000001")})
        pool_mock = MagicMock()
        pool_mock.acquire = MagicMock(return_value=_async_ctx(conn_mock))

        required = await policy.is_repo_indexing_required(
            pool=pool_mock,
            full_name="pallets/flask",
            commit_sha="abc12345",
        )
        assert not required  # Unchanged SHA -> Indexing NOT required

    @pytest.mark.anyio
    async def test_is_repo_indexing_required_returns_true_if_no_active_snapshot(self):
        policy = IndexingPolicy()

        conn_mock = AsyncMock()
        conn_mock.fetchrow = AsyncMock(return_value=None)
        pool_mock = MagicMock()
        pool_mock.acquire = MagicMock(return_value=_async_ctx(conn_mock))

        required = await policy.is_repo_indexing_required(
            pool=pool_mock,
            full_name="pallets/flask",
            commit_sha="new_sha_999",
        )
        assert required  # New SHA -> Indexing required


# ── Helper Context Manager ───────────────────────────────────────────────────

class _async_ctx:
    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *args):
        pass


# ── Vector Indexer Pipeline Integration Test (Mocked DB) ──────────────────────

class TestVectorIndexerPipeline:

    @pytest.mark.anyio
    async def test_index_qualified_repository_flow(self):
        chunked_repo = make_sample_chunked_repo()

        conn_mock = AsyncMock()
        conn_mock.fetchrow = AsyncMock(return_value={"id": UUID("00000000-0000-0000-0000-000000000001")})
        conn_mock.fetchval = AsyncMock(return_value=UUID("11111111-1111-1111-1111-111111111111"))
        conn_mock.executemany = AsyncMock(return_value=None)
        conn_mock.execute = AsyncMock(return_value=None)

        pool_mock = MagicMock()
        pool_mock.acquire = MagicMock(return_value=_async_ctx(conn_mock))

        fake_vector = [0.1] * 768

        with patch("app.intelligence.pipeline_vector_index.embed_batch", return_value=[fake_vector]):
            snapshot_id = await index_qualified_repository(
                pool=pool_mock,
                full_name="pallets/flask",
                chunked_repo=chunked_repo,
                commit_sha="commit_sha_123",
            )

        assert snapshot_id == UUID("11111111-1111-1111-1111-111111111111")
        conn_mock.fetchval.assert_called_once()
        conn_mock.executemany.assert_called_once()
        conn_mock.execute.assert_any_call(
            "SELECT activate_snapshot($1::uuid, $2::text)",
            UUID("11111111-1111-1111-1111-111111111111"),
            "pallets/flask",
        )
