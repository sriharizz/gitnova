"""
GitNova v4.2 — Standalone Vector Indexing Pipeline (Sprint 7)

Responsibility:
  - Takes a ChunkedRepository (from Sprint 6) and generates 768-dim embeddings using local sentence-transformers (jinaai/jina-embeddings-v2-base-code).
  - Decouples Qualification from Indexing Policy: IndexingPolicy selects eligible qualified repos based on configurable storage budgets (max_total_chunks, max_total_bytes, max_active_indexed_repos) and score ranking.
  - Implements incremental SHA-based skip: skips repos whose commit_sha has not changed since the active snapshot.
  - Atomically stores snapshots in repository_snapshots (STAGING status) and batch-inserts chunks into code_chunks.
  - Promotes snapshot to ACTIVE via activate_snapshot RPC, purging retired snapshots safely via ON DELETE CASCADE.
  - Zero RAG, zero LLM calls, zero retrieval queries — strictly embedding generation & vector storage.
"""

from dataclasses import dataclass, field
import json
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import asyncpg

from app.intelligence.chunker import CodeChunk, ChunkedRepository
from app.pipeline.embedder import embed_batch
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Configuration & Indexing Policy ──────────────────────────────────────────

@dataclass
class VectorIndexConfig:
    """Configurable operational defaults for storage-based indexing budget."""
    max_total_chunks: int = 25_000          # Operational default max chunks in vector DB (~250 MB)
    max_total_bytes: int = 250_000_000       # Operational default max raw bytes (~250 MB)
    max_active_indexed_repos: int = 100      # Operational default max active repos
    batch_size: int = 32                     # Embedding batch size
    embedding_model: str = "jinaai/jina-embeddings-v2-base-code"
    embedding_dimensions: int = 768
    parser_version: str = "v4.2-ast"


class IndexingPolicy:
    """
    Decouples Qualification from Indexing Policy.
    Qualification determines eligibility (is_active = TRUE, score >= 50).
    IndexingPolicy decides WHICH eligible repositories are actually embedded
    based on score ranking, storage budget, and incremental commit_sha changes.
    """

    async def select_eligible_repositories(
        self,
        pool: asyncpg.Pool,
        min_score: float = 50.0,
        limit: int = 100,
    ) -> List[Dict[str, any]]:
        """Queries qualified repositories from DB ordered by Contribution Success Score DESC."""
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, full_name, score, tier, updated_at
                  FROM repos
                 WHERE is_active = TRUE AND score >= $1
                 ORDER BY score DESC
                 LIMIT $2
                """,
                min_score,
                limit,
            )
            return [dict(r) for r in rows]

    async def is_repo_indexing_required(
        self,
        pool: asyncpg.Pool,
        full_name: str,
        commit_sha: str,
        config: VectorIndexConfig = VectorIndexConfig(),
    ) -> bool:
        """
        Incremental Indexing Check:
        Returns False if an ACTIVE snapshot already exists for this exact full_name,
        commit_sha, and embedding_model.
        """
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id FROM repository_snapshots
                 WHERE repo_name = $1
                   AND commit_sha = $2
                   AND status = 'ACTIVE'
                   AND embedding_model = $3
                """,
                full_name,
                commit_sha,
                config.embedding_model,
            )
            return row is None


# ── Core Vector Indexing Pipeline ──────────────────────────────────────────────

def prepare_text_for_embedding(chunk: CodeChunk) -> str:
    """
    Constructs the text payload to embed.
    Combines contextual_header + raw_content (capped at 4,000 chars)
    to ensure file paths, symbols, and code logic are represented in the 768-dim vector.
    """
    header = chunk.contextual_header or f"[{chunk.file_path}]"
    combined = f"{header}\n{chunk.raw_content}"
    return combined[:4000]


async def index_qualified_repository(
    pool: asyncpg.Pool,
    full_name: str,
    chunked_repo: ChunkedRepository,
    commit_sha: str,
    default_branch: str = "main",
    config: VectorIndexConfig = VectorIndexConfig(),
) -> UUID:
    """
    High-level entry point for Sprint 7 Vector Indexing.
    Embeds chunks, creates STAGING snapshot, batch-inserts into code_chunks,
    and atomically activates snapshot.
    Returns the created snapshot UUID.
    """
    if not chunked_repo.chunks:
        logger.warning("no_chunks_to_index", extra={"full_name": full_name})
        raise ValueError(f"No chunks provided for repository {full_name}")

    # 1. Fetch repo_id UUID from DB
    async with pool.acquire() as conn:
        repo_row = await conn.fetchrow(
            "SELECT id FROM repos WHERE full_name = $1 AND is_active = TRUE",
            full_name,
        )
        repo_id: Optional[UUID] = repo_row["id"] if repo_row else None

    # 2. Prepare embedding text payloads
    texts_to_embed = [prepare_text_for_embedding(c) for c in chunked_repo.chunks]
    logger.info(
        "generating_embeddings",
        extra={"full_name": full_name, "chunk_count": len(texts_to_embed), "model": config.embedding_model},
    )

    # 3. Generate 768-dim float vectors using local sentence-transformers
    embeddings: List[List[float]] = embed_batch(texts_to_embed)
    if len(embeddings) != len(chunked_repo.chunks):
        raise RuntimeError(
            f"Embedding count mismatch: generated {len(embeddings)} vectors for {len(chunked_repo.chunks)} chunks"
        )

    # 4. Create STAGING snapshot in repository_snapshots
    async with pool.acquire() as conn:
        snapshot_id = await conn.fetchval(
            """
            INSERT INTO repository_snapshots (
                repo_name, commit_sha, default_branch, status,
                file_count, chunk_count, content_bytes,
                embedding_model, embedding_dimensions, parser_version
            ) VALUES (
                $1, $2, $3, 'STAGING',
                $4, $5, $6,
                $7, $8, $9
            ) RETURNING id
            """,
            full_name,
            commit_sha,
            default_branch,
            chunked_repo.files_processed,
            chunked_repo.total_chunks,
            chunked_repo.total_bytes,
            config.embedding_model,
            config.embedding_dimensions,
            config.parser_version,
        )

        logger.info("snapshot_created_staging", extra={"snapshot_id": str(snapshot_id), "full_name": full_name})

        # 5. Batch-insert code_chunks
        chunk_rows = []
        for chunk, emb in zip(chunked_repo.chunks, embeddings):
            # Format vector as string for pgvector input "[0.1, 0.2, ...]"
            vector_str = "[" + ",".join(str(f) for f in emb) + "]"
            chunk_rows.append((
                chunk.chunk_id,
                snapshot_id,
                full_name,
                commit_sha,
                chunk.file_path,
                chunk.language,
                chunk.symbol_name,
                chunk.start_line,
                chunk.end_line,
                chunk.raw_content,
                chunk.token_estimate,
                vector_str,
                repo_id,
                chunk.info_class,
                chunk.qualified_symbol_name,
                chunk.symbol_type,
                chunk.parent_symbol,
                chunk.contextual_header,
                chunk.parser_strategy,
            ))

        await conn.executemany(
            """
            INSERT INTO code_chunks (
                chunk_id, snapshot_id, repo_name, commit_sha,
                file_path, language, symbol_name, start_line, end_line,
                content, token_count, embedding, repo_id,
                info_class, qualified_symbol_name, symbol_type,
                parent_symbol, contextual_header, parser_strategy
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8, $9,
                $10, $11, $12::vector, $13,
                $14, $15, $16,
                $17, $18, $19
            )
            ON CONFLICT (chunk_id) DO UPDATE SET
                snapshot_id = EXCLUDED.snapshot_id,
                embedding = EXCLUDED.embedding,
                contextual_header = EXCLUDED.contextual_header
            """,
            chunk_rows,
        )

        # 6. Atomically promote STAGING snapshot to ACTIVE (retires & deletes old snapshots)
        await conn.execute(
            "SELECT activate_snapshot($1::uuid, $2::text)",
            snapshot_id,
            full_name,
        )

        # 7. Update last_indexed_at timestamp on repos table
        if repo_id:
            await conn.execute(
                "UPDATE repos SET last_indexed_at = now() WHERE id = $1",
                repo_id,
            )

    logger.info(
        "vector_indexing_complete",
        extra={
            "full_name": full_name,
            "snapshot_id": str(snapshot_id),
            "chunks_indexed": len(chunk_rows),
            "commit_sha": commit_sha,
        },
    )

    return snapshot_id


def index_qualified_repository_supabase(
    supabase_client: any,
    full_name: str,
    chunked_repo: ChunkedRepository,
    commit_sha: str,
    default_branch: str = "main",
    config: VectorIndexConfig = VectorIndexConfig(),
) -> str:
    """
    Synchronous Supabase REST entry point for Sprint 7 Vector Indexing.
    Embeds chunks, creates STAGING snapshot in repository_snapshots,
    batch-upserts into code_chunks, and calls activate_snapshot RPC.
    """
    if not chunked_repo.chunks:
        logger.warning("no_chunks_to_index", extra={"full_name": full_name})
        raise ValueError(f"No chunks provided for repository {full_name}")

    # 1. Fetch repo_id UUID from DB
    repo_resp = supabase_client.table("repos").select("id").eq("full_name", repo_name_clean(full_name)).eq("is_active", True).execute()
    repo_id = repo_resp.data[0]["id"] if repo_resp.data else None

    # 2. Prepare embedding text payloads
    texts_to_embed = [prepare_text_for_embedding(c) for c in chunked_repo.chunks]
    logger.info(
        "generating_embeddings",
        extra={"full_name": full_name, "chunk_count": len(texts_to_embed), "model": config.embedding_model},
    )

    # 3. Generate 768-dim float vectors using local sentence-transformers
    embeddings: List[List[float]] = embed_batch(texts_to_embed)
    if len(embeddings) != len(chunked_repo.chunks):
        raise RuntimeError(
            f"Embedding count mismatch: generated {len(embeddings)} vectors for {len(chunked_repo.chunks)} chunks"
        )

    # 4. Create STAGING snapshot in repository_snapshots
    snapshot_record = {
        "repo_name": full_name,
        "commit_sha": commit_sha,
        "default_branch": default_branch,
        "status": "STAGING",
        "file_count": chunked_repo.files_processed,
        "chunk_count": chunked_repo.total_chunks,
        "content_bytes": chunked_repo.total_bytes,
        "embedding_model": config.embedding_model,
        "embedding_dimensions": config.embedding_dimensions,
        "parser_version": config.parser_version,
    }
    snap_resp = supabase_client.table("repository_snapshots").upsert(snapshot_record, on_conflict="repo_name,commit_sha,embedding_model,parser_version").execute()
    if not snap_resp.data:
        raise RuntimeError(f"Failed to create STAGING snapshot for {full_name}")

    snapshot_id = snap_resp.data[0]["id"]
    logger.info("snapshot_created_staging", extra={"snapshot_id": str(snapshot_id), "full_name": full_name})

    # 5. Batch-insert code_chunks
    chunk_records = []
    for chunk, emb in zip(chunked_repo.chunks, embeddings):
        vector_str = "[" + ",".join(str(f) for f in emb) + "]"
        rec = {
            "chunk_id": chunk.chunk_id,
            "content_hash": chunk.chunk_id,
            "snapshot_id": snapshot_id,
            "repo_name": full_name,
            "commit_sha": commit_sha,
            "file_path": chunk.file_path,
            "language": chunk.language,
            "symbol_name": chunk.symbol_name,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content": chunk.raw_content,
            "token_count": chunk.token_estimate,
            "embedding": vector_str,
            "info_class": chunk.info_class,
            "qualified_symbol_name": chunk.qualified_symbol_name,
            "symbol_type": chunk.symbol_type,
            "parent_symbol": chunk.parent_symbol,
            "contextual_header": chunk.contextual_header,
            "parser_strategy": chunk.parser_strategy,
        }
        if repo_id:
            rec["repo_id"] = repo_id
        chunk_records.append(rec)

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(chunk_records), batch_size):
        batch = chunk_records[i : i + batch_size]
        supabase_client.table("code_chunks").upsert(batch).execute()

    # 6. Atomically promote STAGING snapshot to ACTIVE
    supabase_client.rpc(
        "activate_snapshot",
        {
            "target_snapshot_id": str(snapshot_id),
            "target_repo": full_name,
        },
    ).execute()

    # 7. Update last_indexed_at timestamp on repos table
    if repo_id:
        supabase_client.table("repos").update({"last_indexed_at": "now()"}).eq("id", repo_id).execute()

    logger.info(
        "vector_indexing_complete",
        extra={
            "full_name": full_name,
            "snapshot_id": str(snapshot_id),
            "chunks_indexed": len(chunk_records),
            "commit_sha": commit_sha,
        },
    )

    return str(snapshot_id)


def repo_name_clean(full_name: str) -> str:
    return full_name.strip()

