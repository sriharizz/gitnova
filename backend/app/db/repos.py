"""
GitNova v4.2 — Repository DB Queries

All SQL queries for the repos table.
Called by main.py endpoint handlers — keeps route code thin.

Design:
  - All queries use parameterized SQL (no f-strings with user input).
  - asyncpg returns asyncpg.Record objects; row_to_repo() converts to RepoOut.
  - score_breakdown is stored as JSONB; deserialized to ScoreBreakdown.
  - score_explanation is stored as JSONB array; deserialized to List[str].
  - topics is stored as TEXT[]; asyncpg returns as Python list directly.
  - unavailable_metrics is stored as TEXT[]; asyncpg returns as Python list.
"""

import json
from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import HTTPException

from app.main import RepoOut, ScoreBreakdown
from app.core.logging import get_logger

logger = get_logger(__name__)

_BASE_SELECT = """
    SELECT
        id,
        full_name,
        tier,
        score,
        score_grade,
        score_breakdown,
        score_explanation,
        complexity_estimate,
        COALESCE(unavailable_metrics, '{}') AS unavailable_metrics,
        COALESCE(topics, '{}') AS topics,
        stars,
        language,
        description,
        last_scored_at
    FROM repos
    WHERE is_active = TRUE
"""


def _row_to_repo(row: asyncpg.Record) -> RepoOut:
    """Convert an asyncpg Record to a RepoOut Pydantic model."""
    # score_breakdown is JSONB — asyncpg returns a string; parse it
    breakdown_raw = row["score_breakdown"]
    if isinstance(breakdown_raw, str):
        breakdown_raw = json.loads(breakdown_raw)

    # score_explanation is JSONB — asyncpg returns a string; parse it
    explanation_raw = row["score_explanation"]
    if isinstance(explanation_raw, str):
        explanation_raw = json.loads(explanation_raw)
    if not isinstance(explanation_raw, list):
        explanation_raw = []

    return RepoOut(
        id=row["id"],
        full_name=row["full_name"],
        tier=row["tier"],
        score=row["score"],
        score_grade=row["score_grade"],
        score_breakdown=ScoreBreakdown(**breakdown_raw),
        score_explanation=explanation_raw,
        complexity_estimate=row["complexity_estimate"],
        unavailable_metrics=list(row["unavailable_metrics"] or []),
        topics=list(row["topics"] or []),
        stars=row["stars"],
        language=row["language"],
        description=row["description"],
        last_scored_at=row["last_scored_at"],
    )


async def fetch_repos(
    conn: asyncpg.Connection,
    tier: Optional[str],
    min_score: Optional[int],
    language: Optional[str],
    limit: int,
    offset: int,
) -> List[RepoOut]:
    """
    Fetch repositories from the DB with optional filters.
    Ordered by score DESC — highest Contribution Success Score first.
    """
    conditions = ["is_active = TRUE"]
    params: list = []
    p = 1  # parameter index

    if tier is not None:
        conditions.append(f"tier = ${p}")
        params.append(tier)
        p += 1

    if min_score is not None:
        conditions.append(f"score >= ${p}")
        params.append(float(min_score))
        p += 1

    if language is not None:
        conditions.append(f"LOWER(language) = LOWER(${p})")
        params.append(language)
        p += 1

    where = " AND ".join(conditions)

    sql = f"""
        SELECT
            id,
            full_name,
            tier,
            score,
            score_grade,
            score_breakdown,
            score_explanation,
            complexity_estimate,
            COALESCE(unavailable_metrics, '{{}}') AS unavailable_metrics,
            COALESCE(topics, '{{}}') AS topics,
            stars,
            language,
            description,
            last_scored_at
        FROM repos
        WHERE {where}
        ORDER BY score DESC
        LIMIT ${p} OFFSET ${p + 1}
    """
    params.extend([limit, offset])

    logger.info("fetch_repos_query", extra={
        "tier": tier, "min_score": min_score, "language": language,
        "limit": limit, "offset": offset,
    })

    rows = await conn.fetch(sql, *params)
    return [_row_to_repo(row) for row in rows]


async def fetch_repo_by_id(
    conn: asyncpg.Connection,
    repo_id: UUID,
) -> RepoOut:
    """
    Fetch a single active repository by UUID.
    Raises 404 if not found or not active.
    """
    sql = f"""
        SELECT
            id,
            full_name,
            tier,
            score,
            score_grade,
            score_breakdown,
            score_explanation,
            complexity_estimate,
            COALESCE(unavailable_metrics, '{{}}') AS unavailable_metrics,
            COALESCE(topics, '{{}}') AS topics,
            stars,
            language,
            description,
            last_scored_at
        FROM repos
        WHERE id = $1 AND is_active = TRUE
    """
    row = await conn.fetchrow(sql, repo_id)

    if row is None:
        logger.info("repo_not_found", extra={"repo_id": str(repo_id)})
        raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found")

    return _row_to_repo(row)
