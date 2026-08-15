"""
GitNova v4.2 — Async GitHub API Client

Designed for use inside GitHub Actions workers (async, not the FastAPI API).
The API never calls GitHub directly — only the workers do.

Features:
  - Authenticated requests (5,000 req/hour vs 60 unauthenticated)
  - Rate limit tracking via X-RateLimit-Remaining header
  - Proactive backoff before hitting the limit
  - Exponential backoff + retry on 429 / 5xx
  - ETag / If-None-Match support — 304 responses cost nothing against rate limit

Usage:
    async with GitHubClient() as client:
        repo = await client.get_repo("pallets/flask")
        issues = await client.get_issues("pallets/flask")
"""

import asyncio
import time
import random
import httpx
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://api.github.com"
MAX_RETRIES = 3
BASE_DELAY = 2.0


class GitHubRateLimitError(Exception):
    """Raised when rate limit is exhausted and reset is too far away."""
    pass


class GitHubAPIError(Exception):
    """Raised on unrecoverable GitHub API errors."""
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


class GitHubClient:
    """
    Async GitHub REST API client.

    Use as an async context manager:
        async with GitHubClient() as client:
            data = await client.get_repo("pallets/flask")
    """

    def __init__(self):
        self._token = settings.github_token
        self._client: Optional[httpx.AsyncClient] = None

        # Rate limit state — updated on every response
        self._remaining: int = 5000 if self._token else 60
        self._reset_at: float = 0.0

        # In-memory ETag cache: url → {"etag": str, "data": Any}
        # Workers are short-lived processes — DB-backed persistence is in the
        # old pipeline client. For the new async client, in-memory is sufficient
        # within a single run. Cross-run persistence uses etag_cache table (Sprint 3).
        self._etag_cache: Dict[str, Dict[str, Any]] = {}

    async def __aenter__(self) -> "GitHubClient":
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        else:
            logger.warning("github_no_token", extra={"msg": "Unauthenticated — 60 req/hour limit"})

        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers=headers,
            timeout=httpx.Timeout(10.0, read=30.0),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    # ── Rate limit ────────────────────────────────────────────────────────────

    def _update_rate_limit(self, headers: httpx.Headers) -> None:
        """Read X-RateLimit-* headers and update local state."""
        try:
            if "X-RateLimit-Remaining" in headers:
                self._remaining = int(headers["X-RateLimit-Remaining"])
            if "X-RateLimit-Reset" in headers:
                self._reset_at = float(headers["X-RateLimit-Reset"])
        except (ValueError, TypeError):
            pass

    async def _check_rate_limit(self) -> None:
        """Proactively pause if fewer than 50 requests remain."""
        if self._remaining <= 50 and time.time() < self._reset_at:
            wait = int(self._reset_at - time.time()) + 1
            if wait <= 300:  # Wait up to 5 minutes
                logger.warning("rate_limit_pause", extra={"remaining": self._remaining, "wait_s": wait})
                await asyncio.sleep(wait)
            else:
                raise GitHubRateLimitError(
                    f"Rate limit exhausted. Resets in {wait}s — deferring to next run."
                )

    # ── Core request ─────────────────────────────────────────────────────────

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """
        Make an authenticated GitHub API request with retry + ETag support.
        Returns parsed JSON or None (on 304 Not Modified with no cached data).
        """
        assert self._client is not None, "Use as async context manager: async with GitHubClient()"

        url = path if path.startswith("http") else f"{BASE_URL}{path}"
        await self._check_rate_limit()

        # Attach ETag for GET requests if we have a cached version
        if method.upper() == "GET" and url in self._etag_cache:
            kwargs.setdefault("headers", {})
            kwargs["headers"]["If-None-Match"] = self._etag_cache[url]["etag"]

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self._client.request(method, url, **kwargs)
                self._update_rate_limit(response.headers)

                # 304 Not Modified — return cached data (costs nothing against rate limit)
                if response.status_code == 304:
                    cached = self._etag_cache.get(url, {})
                    logger.info("github_cache_hit", extra={"url": url})
                    return cached.get("data", [])

                # Success
                if 200 <= response.status_code < 300:
                    data = response.json()
                    # Cache ETag for next call
                    if "ETag" in response.headers:
                        self._etag_cache[url] = {"etag": response.headers["ETag"], "data": data}
                    logger.info("github_request_ok", extra={
                        "path": path,
                        "status": response.status_code,
                        "remaining": self._remaining,
                    })
                    return data

                # Rate limited
                if response.status_code in (429, 403) and self._remaining == 0:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning("github_rate_limited", extra={"retry_after": retry_after, "attempt": attempt})
                    await asyncio.sleep(retry_after)
                    continue

                # Transient server error — exponential backoff
                if response.status_code >= 500:
                    delay = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0.1, 1.0)
                    logger.warning("github_server_error", extra={"status": response.status_code, "delay": delay, "attempt": attempt})
                    await asyncio.sleep(delay)
                    continue

                # 404 — return None gracefully (missing files are expected)
                if response.status_code == 404:
                    return None

                # Other 4xx — unrecoverable
                raise GitHubAPIError(
                    f"GitHub API error {response.status_code} for {path}",
                    status_code=response.status_code,
                )

            except httpx.RequestError as e:
                if attempt == MAX_RETRIES:
                    raise GitHubAPIError(f"Connection failed: {e}", status_code=500)
                delay = BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0.1, 1.0)
                logger.warning("github_connection_error", extra={"error": str(e), "delay": delay})
                await asyncio.sleep(delay)

        raise GitHubAPIError(f"Failed after {MAX_RETRIES} attempts: {path}", status_code=500)

    # ── Public API methods ────────────────────────────────────────────────────

    async def get_repo(self, full_name: str) -> Optional[Dict]:
        """GET /repos/{owner}/{repo} — basic metadata."""
        return await self._request("GET", f"/repos/{full_name}")

    async def get_issues(self, full_name: str, state: str = "open", since_days: int = 90) -> List[Dict]:
        """GET /repos/{owner}/{repo}/issues — open issues, last N days."""
        import datetime
        since = (datetime.datetime.utcnow() - datetime.timedelta(days=since_days)).isoformat() + "Z"
        result = await self._request("GET", f"/repos/{full_name}/issues", params={
            "state": state,
            "since": since,
            "per_page": 100,
            "sort": "updated",
            "direction": "desc",
        })
        return result if isinstance(result, list) else []

    async def get_pulls(self, full_name: str, state: str = "all") -> List[Dict]:
        """GET /repos/{owner}/{repo}/pulls — for PR merge rate calculation."""
        result = await self._request("GET", f"/repos/{full_name}/pulls", params={
            "state": state,
            "per_page": 50,
            "sort": "updated",
            "direction": "desc",
        })
        return result if isinstance(result, list) else []

    async def get_labels(self, full_name: str) -> List[Dict]:
        """GET /repos/{owner}/{repo}/labels — check for good-first-issue label."""
        result = await self._request("GET", f"/repos/{full_name}/labels", params={"per_page": 100})
        return result if isinstance(result, list) else []

    async def get_contributors(self, full_name: str) -> List[Dict]:
        """GET /repos/{owner}/{repo}/contributors — community health signal."""
        result = await self._request("GET", f"/repos/{full_name}/contributors", params={"per_page": 50, "anon": "false"})
        return result if isinstance(result, list) else []

    async def get_releases(self, full_name: str) -> List[Dict]:
        """GET /repos/{owner}/{repo}/releases — recency signal."""
        result = await self._request("GET", f"/repos/{full_name}/releases", params={"per_page": 5})
        return result if isinstance(result, list) else []

    async def file_exists(self, full_name: str, path: str) -> bool:
        """
        Check if a file exists in the repo root.
        Returns True/False. Used to check CONTRIBUTING.md, CODE_OF_CONDUCT.md, README.md.
        """
        result = await self._request("GET", f"/repos/{full_name}/contents/{path}")
        return result is not None

    async def search_repos(self, query: str, per_page: int = 30) -> List[Dict]:
        """
        GET /search/repositories — discover repos matching beginner-friendly signals.
        Returns list of repo items (not the full response wrapper).
        """
        result = await self._request("GET", "/search/repositories", params={
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": per_page,
        })
        if isinstance(result, dict) and "items" in result:
            return result["items"]
        return []

    @property
    def rate_limit_remaining(self) -> int:
        return self._remaining
