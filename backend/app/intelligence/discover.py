"""
GitNova v4.2 — Repository Discovery

ENGINEERING PHILOSOPHY & ARCHITECTURE:
    Repository Discovery has ONE responsibility: build a broad, diverse,
    high-quality candidate pool.

    Separation of Concerns:
      Discovery       → "Is this repo active, public, and real?" (Recall)
      Qualification   → "Is this repo healthy for a contributor?" (Quality + Complexity)
      Personalization → "Is this repo right for THIS user?" (User Fit)

    Why Deterministic?
      We intentionally kept Discovery deterministic because repository discovery is a
      structured retrieval problem. GitHub already indexes repositories efficiently.
      As AI Engineers, we use AI only where semantic reasoning provides measurable value
      (downstream in Issue RAG and LLM Mentoring).

    Star Usage:
      Stars are used ONLY as a sampling / noise-reduction floor (min_stars: 50) to filter
      out empty or toy sandboxes. Stars do NOT represent quality, tier, or complexity.

    Allocation:
      ALL configured queries execute, then a round-robin allocation selects candidates
      from per-query pools with slot redistribution. This ensures every language and
      strategy archetype (libraries, frameworks, tools) gets candidate representation.

Configuration:
    All parameters live in config/discovery_config.yaml.

Usage:
    async with GitHubClient() as client:
        candidates = await discover_repos(client, known_repos={"pallets/flask"})
"""

import asyncio
import datetime
import pathlib
from typing import Dict, List, Set

import yaml

from app.clients.github import GitHubClient
from app.core.logging import get_logger

logger = get_logger(__name__)

# Path to config — relative to project root
_CONFIG_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "config" / "discovery_config.yaml"


def _load_config() -> dict:
    """Load discovery configuration from YAML. Fails loudly if missing."""
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Discovery config not found at {_CONFIG_PATH}. "
            "Expected: config/discovery_config.yaml"
        )
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def _build_queries(config: dict) -> List[str]:
    """
    Dynamically build GitHub Search queries from config.

    Produces two types:
      1. Per-language queries — one per language in config (Language Coverage)
      2. Cross-language queries — archetype & ecosystem coverage (library, framework, tool)

    No topic filters for beginner-friendliness. No upper star limits.
    The Qualification Engine decides what is good.
    """
    min_stars = config["min_stars"]
    activity_days = config["activity_window_days"]
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=activity_days)).strftime("%Y-%m-%d")

    queries: List[str] = []

    # Per-language queries — Language Coverage
    for lang in config.get("languages", []):
        queries.append(f"language:{lang} stars:>{min_stars} pushed:>{cutoff} archived:false")

    # Cross-language queries — Archetype & Ecosystem Coverage
    for template in config.get("cross_language_queries", []):
        query = template.replace("{min_stars}", str(min_stars)).replace("{cutoff_date}", cutoff)
        queries.append(query)

    return queries


def _balanced_select(
    pools: Dict[int, List[str]],
    max_candidates: int,
) -> List[str]:
    """
    Round-robin selection across query pools with slot redistribution.

    Algorithm:
      1. Calculate fair_share = max_candidates // number_of_non_empty_pools
      2. First pass: take up to fair_share from each pool
      3. Collect unused slots (pool had fewer than fair_share candidates)
      4. Redistribute unused slots across pools that still have remaining candidates
      5. Repeat redistribution until budget is filled or all pools exhausted

    This ensures every configured query gets representation. Early languages
    cannot dominate the candidate pool. Cross-language queries always run.
    """
    candidates: List[str] = []
    remaining: Dict[int, List[str]] = {k: list(v) for k, v in pools.items() if v}

    budget = max_candidates

    while budget > 0 and remaining:
        fair_share = max(1, budget // len(remaining))
        unused_slots = 0
        exhausted_pools: List[int] = []

        for pool_idx in sorted(remaining.keys()):
            if budget <= 0:
                break

            pool = remaining[pool_idx]
            take = min(fair_share, len(pool), budget)
            candidates.extend(pool[:take])
            budget -= take

            if take < fair_share:
                unused_slots += fair_share - take

            remaining[pool_idx] = pool[take:]
            if not remaining[pool_idx]:
                exhausted_pools.append(pool_idx)

        for idx in exhausted_pools:
            del remaining[idx]

    return candidates


async def discover_repos(
    client: GitHubClient,
    known_repos: Set[str],
) -> List[str]:
    """
    Discover new repository candidates via GitHub Search API.

    Args:
        client:      Authenticated GitHubClient (async context manager)
        known_repos: Set of full_names already in our DB — skipped to avoid re-scoring

    Returns:
        Deduplicated list of repo full_names.
        Example: ["encode/httpx", "tiangolo/fastapi", ...]
        Ready to pass directly to the Repository Qualification Engine.
    """
    config = _load_config()
    queries = _build_queries(config)

    max_candidates: int = config.get("max_candidates_per_run", 150)
    per_query_limit: int = config.get("per_query_limit", 30)
    pause_ms: int = config.get("search_pause_ms", 300)

    logger.info("discovery_started", extra={
        "total_queries": len(queries),
        "max_candidates": max_candidates,
        "known_repos": len(known_repos),
        "pause_ms": pause_ms,
    })

    # ── Phase 1: Execute ALL queries, collect into per-query pools ─────────
    pools: Dict[int, List[str]] = {}
    seen: Set[str] = set()

    for idx, query in enumerate(queries):
        pool: List[str] = []
        try:
            items = await client.search_repos(query, per_page=per_query_limit)

            for item in items:
                full_name: str = item.get("full_name", "")
                if not full_name:
                    continue

                if full_name in known_repos or full_name in seen:
                    continue

                if item.get("archived") or item.get("disabled") or item.get("private"):
                    continue

                seen.add(full_name)
                pool.append(full_name)

            logger.info("discovery_query_done", extra={
                "query_index": idx,
                "query": query[:80],
                "results_returned": len(items),
                "unique_new": len(pool),
                "rate_limit_remaining": client.rate_limit_remaining,
            })

        except Exception as e:
            logger.warning("discovery_query_failed", extra={
                "query_index": idx,
                "query": query[:80],
                "error": str(e),
            })

        pools[idx] = pool

        if pause_ms > 0:
            await asyncio.sleep(pause_ms / 1000)

    # ── Phase 2: Balanced round-robin allocation ──────────────────────────
    candidates = _balanced_select(pools, max_candidates)

    logger.info("discovery_complete", extra={
        "candidates_found": len(candidates),
        "queries_run": len(queries),
        "pools_with_results": sum(1 for p in pools.values() if p),
        "pool_sizes": {str(k): len(v) for k, v in pools.items()},
        "rate_limit_remaining": client.rate_limit_remaining,
    })

    return candidates
