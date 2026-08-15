"""
GitNova v4.2 — Standalone Qualified Repository Ingestion & Structural Analysis Pipeline

Decoupled Ingestion Boundary:
  - Does NOT run during cheap weekly discovery/qualification runs.
  - Executed only for repositories that have passed qualification and require structural analysis.
  - Downloads archive, extracts file tree & LOC, refines onboarding complexity in DB.
  - Updates complexity_estimate and complexity_signals (setting complexity_source="structural").
"""

import json
from typing import Optional
import asyncpg

from app.intelligence.ingestor import ingest_repository_archive, RepoDocumentCorpus
from app.intelligence.scorer import RepositoryScorer
from app.core.logging import get_logger

logger = get_logger(__name__)


async def ingest_qualified_repo(
    pool: asyncpg.Pool,
    full_name: str,
    github_token: Optional[str] = None,
) -> RepoDocumentCorpus:
    """
    Ingests and structurally analyzes a qualified repository.
    Updates database onboarding complexity using verified structural ground-truth.
    Returns the RepoDocumentCorpus ready for future chunking.
    """
    # 1. Verify repo exists in DB and is active
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, score, complexity_estimate, complexity_signals FROM repos WHERE full_name = $1 AND is_active = TRUE",
            full_name,
        )
        if row is None:
            raise ValueError(f"Repository {full_name} is not qualified or active in DB.")

        provisional_complexity = row["complexity_estimate"] or 50.0
        provisional_signals_raw = row["complexity_signals"] or "{}"
        if isinstance(provisional_signals_raw, str):
            provisional_signals = json.loads(provisional_signals_raw)
        else:
            provisional_signals = dict(provisional_signals_raw)

        score = row["score"] or 0.0

    # 2. Perform safe archive download & structural analysis
    logger.info("starting_repo_ingestion", extra={"full_name": full_name})
    corpus = ingest_repository_archive(full_name, github_token=github_token)

    # 3. Refine onboarding complexity using structural metrics
    scorer = RepositoryScorer()
    refined_complexity, refined_signals = scorer.refine_complexity_with_structural_metrics(
        provisional_complexity=provisional_complexity,
        provisional_signals=provisional_signals,
        file_count=corpus.metrics.file_count,
        total_loc=corpus.metrics.total_loc,
        max_directory_depth=corpus.metrics.max_directory_depth,
    )

    # 4. Re-assign tier using refined structural complexity
    refined_tier = scorer._assign_tier(score, refined_complexity)

    # 5. Persist structural refinement to DB
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE repos
               SET complexity_estimate = $1,
                   complexity_signals  = $2::jsonb,
                   tier                = $3,
                   updated_at          = now()
             WHERE full_name = $4
            """,
            refined_complexity,
            json.dumps(refined_signals),
            refined_tier,
            full_name,
        )

    logger.info(
        "repo_ingestion_complete",
        extra={
            "full_name": full_name,
            "provisional_complexity": provisional_complexity,
            "refined_complexity": refined_complexity,
            "refined_tier": refined_tier,
            "loc": corpus.metrics.total_loc,
            "files": corpus.metrics.file_count,
        },
    )

    return corpus
