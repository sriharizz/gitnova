"""
GitNova v4.2 — Repository Qualification Pipeline

Weekly GitHub Actions worker: discover → collect → score → store.

This script is NOT the FastAPI app. It runs as a scheduled cron job.
It writes to Supabase. The API reads what this script writes.

Pipeline steps:
  1. Load known repos from DB (to skip re-scoring unchanged repos)
  2. Discover new candidates (GitHub Search API)
  3. For each candidate: collect metrics → score → upsert to repos table
  4. Log pipeline run to pipeline_runs table

Entry point:
  python -m app.intelligence.run
  (or via GitHub Actions: python backend/app/intelligence/run.py)

Environment variables required:
  DATABASE_URL   — Supabase connection string
  GITHUB_TOKEN   — GitHub personal access token (5000 req/hour)
"""

import asyncio
import asyncpg
import json
import sys
import time
from typing import Set

from app.clients.github import GitHubClient
from app.core.config import settings
from app.core.logging import get_logger
from app.intelligence.collector import collect_repo_metrics
from app.intelligence.discover import discover_repos
from app.intelligence.scorer import RepositoryScorer

logger = get_logger(__name__)


async def load_known_repos(pool: asyncpg.Pool) -> Set[str]:
    """
    Load all repo full_names already in our DB.
    These will be skipped during discovery to avoid re-discovering them.
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT full_name FROM repos WHERE is_active = TRUE")
    known = {row["full_name"] for row in rows}
    logger.info("known_repos_loaded", extra={"count": len(known)})
    return known


async def upsert_repo(pool: asyncpg.Pool, full_name: str, result) -> None:
    """
    Upsert a scored repo into the repos table.
    Uses ON CONFLICT DO UPDATE so re-running the pipeline is safe.
    """
    m = result.metrics
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO repos (
                full_name, stars, forks, language, license_spdx, topics,
                score, score_grade, score_breakdown, score_explanation,
                tier, complexity_estimate, complexity_signals,
                unavailable_metrics,
                raw_metrics, is_active, last_scored_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6,
                $7, $8, $9::jsonb, $10::jsonb,
                $11, $12, $13::jsonb,
                $14,
                $15::jsonb, TRUE, now(), now()
            )
            ON CONFLICT (full_name) DO UPDATE SET
                stars               = EXCLUDED.stars,
                forks               = EXCLUDED.forks,
                language            = EXCLUDED.language,
                license_spdx        = EXCLUDED.license_spdx,
                topics              = EXCLUDED.topics,
                score               = EXCLUDED.score,
                score_grade         = EXCLUDED.score_grade,
                score_breakdown     = EXCLUDED.score_breakdown,
                score_explanation   = EXCLUDED.score_explanation,
                tier                = EXCLUDED.tier,
                complexity_estimate = EXCLUDED.complexity_estimate,
                complexity_signals  = EXCLUDED.complexity_signals,
                unavailable_metrics = EXCLUDED.unavailable_metrics,
                raw_metrics         = EXCLUDED.raw_metrics,
                is_active           = TRUE,
                last_scored_at      = now(),
                updated_at          = now()
            """,
            full_name,
            m.stars,
            m.forks,
            m.language,
            m.license_spdx,
            m.topics,
            result.total,
            result.grade,
            json.dumps(result.breakdown),
            json.dumps(result.explanation),
            result.tier,
            result.complexity_estimate,
            json.dumps(result.complexity_signals),
            result.unavailable_metrics,          # TEXT[] — asyncpg handles list→array
            json.dumps({
                "stars": m.stars,
                "forks": m.forks,
                "open_issues": m.open_issues_count,
                "days_since_push": m.days_since_push,
                "contributor_count": m.contributor_count,
                "has_contributing_md": m.has_contributing_md,
                "has_coc": m.has_code_of_conduct,
                "has_gfi_label": m.has_good_first_issue_label,
            }),
        )


async def log_pipeline_run(
    pool: asyncpg.Pool,
    run_id: str,
    repos_processed: int,
    items_published: int,
    status: str,
    error_log: str = None,
) -> None:
    """Update the pipeline_runs row to record final status."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE pipeline_runs
               SET finished_at      = now(),
                   repos_processed  = $2,
                   items_published  = $3,
                   status           = $4,
                   error_log        = $5
             WHERE id = $1
            """,
            run_id,
            repos_processed,
            items_published,
            status,
            error_log,
        )


async def main() -> None:
    if not settings.has_database:
        logger.error("run_aborted", extra={"reason": "DATABASE_URL not set"})
        sys.exit(1)

    if not settings.has_github:
        logger.warning("run_no_github_token", extra={"msg": "Unauthenticated — 60 req/hour limit"})

    start_time = time.time()
    scorer = RepositoryScorer()

    # ── Connect ───────────────────────────────────────────────────────────────
    pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=5,
        statement_cache_size=0,  # Required for Supabase PgBouncer
    )

    # ── Start pipeline run audit row ──────────────────────────────────────────
    async with pool.acquire() as conn:
        run_id = await conn.fetchval(
            """
            INSERT INTO pipeline_runs (run_type, triggered_by, status)
            VALUES ('repo_qualification', 'github_actions', 'running')
            RETURNING id::text
            """
        )
    logger.info("pipeline_started", extra={"run_id": run_id})

    repos_processed = 0
    items_published = 0
    error_log = None

    try:
        # ── Step 1: Load known repos ──────────────────────────────────────────
        known_repos = await load_known_repos(pool)

        # ── Step 2: Discover candidates ───────────────────────────────────────
        async with GitHubClient() as client:
            candidates = await discover_repos(client, known_repos=known_repos)
            logger.info("discovery_done", extra={"candidates": len(candidates)})

            # ── Step 3: Collect → Score → Store ──────────────────────────────
            for full_name in candidates:
                try:
                    metrics = await collect_repo_metrics(client, full_name)
                    if not metrics:
                        continue

                    result = scorer.score(metrics)
                    repos_processed += 1

                    # Only store repos that pass the quality floor (tier is not None)
                    if result.tier is not None:
                        await upsert_repo(pool, full_name, result)
                        items_published += 1
                        logger.info("repo_stored", extra={
                            "repo": full_name,
                            "score": result.total,
                            "tier": result.tier,
                        })
                    else:
                        logger.info("repo_below_quality_floor", extra={
                            "repo": full_name,
                            "score": result.total,
                            "grade": result.grade,
                        })

                except Exception as e:
                    logger.warning("repo_pipeline_error", extra={"repo": full_name, "error": str(e)})
                    continue

        status = "success"

    except Exception as e:
        error_log = str(e)
        status = "failed"
        logger.error("pipeline_failed", extra={"error": error_log})

    finally:
        await log_pipeline_run(pool, run_id, repos_processed, items_published, status, error_log)
        await pool.close()

    duration = round(time.time() - start_time, 1)
    logger.info("pipeline_complete", extra={
        "run_id": run_id,
        "status": status,
        "repos_processed": repos_processed,
        "items_published": items_published,
        "duration_s": duration,
    })


if __name__ == "__main__":
    asyncio.run(main())
