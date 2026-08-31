"""
GitNova v4.2 — Repository Metrics Collector

Collects all GitHub API signals needed by the scorer for one repository.
Orchestrates the 9 API calls per repo and returns a populated RepoMetrics.

Separation of concerns:
  collector.py  → talks to GitHub, assembles RepoMetrics
  scorer.py     → pure computation, never touches GitHub
  run.py        → orchestrates: discover → collect → score → store

MISSING METRIC SEMANTICS:
  When an API request fails or times out, the corresponding metric is set to `None`
  to distinguish "API request failed / data unavailable" from an observed value of 0 or False.
  Boolean signals (CONTRIBUTING.md, CODE_OF_CONDUCT.md, good-first-issue label) use 3-state
  semantics: True (present), False (confirmed absent via 404/empty), None (API fetch failed).
"""

import datetime
from typing import Optional

from app.clients.github import GitHubClient, GitHubAPIError
from app.intelligence.scorer import RepoMetrics
from app.core.logging import get_logger

logger = get_logger(__name__)


async def collect_repo_metrics(
    client: GitHubClient,
    full_name: str,
) -> Optional[RepoMetrics]:
    """
    Fetch all signals for one repository from GitHub API.

    Makes up to 9 API calls:
      1. GET /repos/{full_name}          — basic metadata
      2. GET /repos/{full_name}/issues   — 90-day window
      3. GET /repos/{full_name}/pulls    — recent PRs for merge rate
      4. GET /repos/{full_name}/contents/CONTRIBUTING.md
      5. GET /repos/{full_name}/contents/CODE_OF_CONDUCT.md
      6. GET /repos/{full_name}/labels   — good-first-issue check
      7. GET /repos/{full_name}/contents/README.md
      8. GET /repos/{full_name}/contributors
      9. GET /repos/{full_name}/releases — recency signal

    Returns None if basic metadata fails or repo is archived/disabled/404.
    If sub-requests fail, fields are set to None (unavailable) instead of 0 or False.
    """
    logger.info("collecting_repo", extra={"repo": full_name})

    # ── 1. Basic metadata (Required) ──────────────────────────────────────────
    try:
        meta = await client.get_repo(full_name)
    except GitHubAPIError as e:
        logger.warning("collect_repo_failed", extra={"repo": full_name, "error": str(e)})
        return None

    if not meta:
        return None

    # Skip archived/disabled repos
    if meta.get("archived") or meta.get("disabled"):
        logger.info("collect_skipped_archived", extra={"repo": full_name})
        return None

    stars             = meta.get("stargazers_count", 0) or 0
    forks             = meta.get("forks_count", 0) or 0
    open_issues_count = meta.get("open_issues_count", 0) or 0
    language          = meta.get("language")
    topics            = meta.get("topics", []) or []
    repo_size_kb      = meta.get("size")
    description       = meta.get("description")

    # License
    license_info = meta.get("license") or {}
    license_spdx = license_info.get("spdx_id") if license_info else None
    if license_spdx in ("NOASSERTION", ""):
        license_spdx = None

    # Days since last push
    pushed_at = meta.get("pushed_at")
    days_since_push = 999
    if pushed_at:
        try:
            pushed_dt = datetime.datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            days_since_push = max(0, (datetime.datetime.now(datetime.timezone.utc) - pushed_dt).days)
        except ValueError:
            pass

    # ── 2. Issues (30-day window) ─────────────────────────────────────────────
    issues_closed_30d: Optional[int] = None
    median_issue_close_days: Optional[float] = None
    try:
        issues = await client.get_issues(full_name, state="closed", since_days=30)
        issues_closed_30d = len([i for i in issues if "pull_request" not in i])
        close_times = []
        for issue in issues:
            if "pull_request" in issue:
                continue
            created = issue.get("created_at")
            closed  = issue.get("closed_at")
            if created and closed:
                try:
                    c_dt = datetime.datetime.fromisoformat(created.replace("Z", "+00:00"))
                    cl_dt = datetime.datetime.fromisoformat(closed.replace("Z", "+00:00"))
                    close_times.append((cl_dt - c_dt).total_seconds() / 86400)
                except ValueError:
                    pass
        if close_times:
            close_times.sort()
            median_issue_close_days = close_times[len(close_times) // 2]
    except Exception as e:
        logger.warning("collect_issues_failed", extra={"repo": full_name, "error": str(e)})

    # ── 3. Pull requests (30-day window) ──────────────────────────────────────
    prs_total_30d: Optional[int] = None
    prs_merged_30d: Optional[int] = None
    avg_pr_merge_days: Optional[float] = None
    try:
        prs = await client.get_pulls(full_name, state="closed")
        prs_total_30d = len(prs)
        merged = [p for p in prs if p.get("merged_at")]
        prs_merged_30d = len(merged)

        merge_times = []
        for pr in merged:
            created = pr.get("created_at")
            merged_at = pr.get("merged_at")
            if created and merged_at:
                try:
                    c_dt = datetime.datetime.fromisoformat(created.replace("Z", "+00:00"))
                    m_dt = datetime.datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                    merge_times.append((m_dt - c_dt).total_seconds() / 86400)
                except ValueError:
                    pass
        if merge_times:
            avg_pr_merge_days = sum(merge_times) / len(merge_times)
    except Exception as e:
        logger.warning("collect_pulls_failed", extra={"repo": full_name, "error": str(e)})

    # ── 4. CONTRIBUTING.md (3-state: True / False / None) ─────────────────────
    has_contributing_md: Optional[bool] = None
    try:
        res = await client.get_contents(full_name, "CONTRIBUTING.md")
        has_contributing_md = (res is not None)
    except Exception as e:
        logger.warning("collect_contributing_failed", extra={"repo": full_name, "error": str(e)})

    # ── 5. CODE_OF_CONDUCT.md (3-state: True / False / None) ──────────────────
    has_code_of_conduct: Optional[bool] = None
    try:
        res = await client.get_contents(full_name, "CODE_OF_CONDUCT.md")
        has_code_of_conduct = (res is not None)
    except Exception as e:
        logger.warning("collect_coc_failed", extra={"repo": full_name, "error": str(e)})

    # ── 6. Labels — good-first-issue check (3-state: True / False / None) ────
    has_good_first_issue_label: Optional[bool] = None
    try:
        labels = await client.get_labels(full_name)
        if labels is not None:
            names = {l.get("name", "").lower() for l in labels}
            gfi_synonyms = {
                "good first issue", "good-first-issue",
                "beginner friendly", "beginner",
                "easy", "starter", "help wanted",
                "first-timers-only", "low-hanging-fruit"
            }
            has_good_first_issue_label = bool(names & gfi_synonyms)
    except Exception as e:
        logger.warning("collect_labels_failed", extra={"repo": full_name, "error": str(e)})

    # ── 7. README length ──────────────────────────────────────────────────────
    readme_length: Optional[int] = None
    try:
        readme = await client.get_contents(full_name, "README.md")
        if readme and isinstance(readme, dict):
            readme_length = readme.get("size", 0) or 0
        elif readme is None:
            readme_length = 0  # Confirmed 404 = no README (observed 0)
    except Exception as e:
        logger.warning("collect_readme_failed", extra={"repo": full_name, "error": str(e)})

    # ── 8. Contributors ───────────────────────────────────────────────────────
    contributor_count: Optional[int] = None
    try:
        contributors = await client.get_contributors(full_name)
        contributor_count = len(contributors)
    except Exception as e:
        logger.warning("collect_contributors_failed", extra={"repo": full_name, "error": str(e)})

    # ── 9. Releases — recency signal ─────────────────────────────────────────
    days_since_release: Optional[int] = None
    try:
        releases = await client.get_releases(full_name)
        if releases:
            published = releases[0].get("published_at")
            if published:
                pub_dt = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
                days_since_release = max(0, (datetime.datetime.now(datetime.timezone.utc) - pub_dt).days)
    except Exception as e:
        logger.warning("collect_releases_failed", extra={"repo": full_name, "error": str(e)})

    metrics = RepoMetrics(
        full_name=full_name,
        stars=stars,
        forks=forks,
        open_issues_count=open_issues_count,
        language=language,
        license_spdx=license_spdx,
        topics=topics,
        repo_size_kb=repo_size_kb,
        description=description,
        days_since_push=days_since_push,
        issues_closed_30d=issues_closed_30d,
        prs_merged_30d=prs_merged_30d,
        prs_total_30d=prs_total_30d,
        avg_pr_merge_days=avg_pr_merge_days,
        median_issue_close_days=median_issue_close_days,
        has_contributing_md=has_contributing_md,
        has_good_first_issue_label=has_good_first_issue_label,
        has_code_of_conduct=has_code_of_conduct,
        readme_length=readme_length,
        contributor_count=contributor_count,
        days_since_release=days_since_release,
    )

    logger.info("collected_repo", extra={
        "repo": full_name,
        "stars": stars,
        "days_since_push": days_since_push,
        "has_contributing_md": has_contributing_md,
        "rate_limit_remaining": client.rate_limit_remaining,
    })

    return metrics
