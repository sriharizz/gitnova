"""
GitNova v4.2 — Sprint 4 API Integration Tests

Tests for GET /repos and GET /repos/{repo_id} using FastAPI TestClient.
The DB pool is patched out — tests exercise the full HTTP → Pydantic
serialization pipeline without touching Supabase.

Run: pytest tests/test_api_repos.py -v
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ── Shared fixtures ───────────────────────────────────────────────────────────

REPO_UUID = UUID("aaaaaaaa-0000-0000-0000-000000000001")
REPO_UUID_2 = UUID("aaaaaaaa-0000-0000-0000-000000000002")

BREAKDOWN_DICT = {
    "activity": 18.0,
    "welcome": 22.0,
    "responsiveness": 15.0,
    "documentation": 12.0,
    "health": 18.0,
}


def _make_mock_row(
    repo_id=REPO_UUID,
    full_name="pallets/flask",
    tier="growing",
    score=85.0,
    score_grade="excellent",
    topics=["python", "flask"],
    complexity_estimate=38.5,
    unavailable_metrics=[],
    stars=72000,
    language="Python",
    description="A web framework",
):
    """Return a dict that mimics an asyncpg.Record."""
    row = MagicMock()
    row.__getitem__ = lambda self, key: {
        "id": repo_id,
        "full_name": full_name,
        "tier": tier,
        "score": score,
        "score_grade": score_grade,
        "score_breakdown": json.dumps(BREAKDOWN_DICT),
        "score_explanation": json.dumps(["✓ Active", "✓ Good docs"]),
        "complexity_estimate": complexity_estimate,
        "unavailable_metrics": unavailable_metrics,
        "topics": topics,
        "stars": stars,
        "language": language,
        "description": description,
        "last_scored_at": datetime(2026, 8, 1, 12, 0, 0),
    }[key]
    return row


# ── Helpers ───────────────────────────────────────────────────────────────────

def _patch_fetch_repos(rows):
    """Patch the DB fetch for list_repos."""
    conn_mock = AsyncMock()
    conn_mock.fetch = AsyncMock(return_value=rows)
    pool_mock = MagicMock()
    pool_mock.acquire = MagicMock(return_value=_async_ctx(conn_mock))
    return pool_mock, conn_mock


def _patch_fetch_repo(row):
    """Patch the DB fetchrow for get_repo."""
    conn_mock = AsyncMock()
    conn_mock.fetchrow = AsyncMock(return_value=row)
    pool_mock = MagicMock()
    pool_mock.acquire = MagicMock(return_value=_async_ctx(conn_mock))
    return pool_mock, conn_mock


class _async_ctx:
    """Minimal async context manager wrapping a mock connection."""
    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *args):
        pass


# ── TestClient (no lifespan — pool patched) ───────────────────────────────────

@pytest.fixture()
def client():
    """TestClient with lifespan disabled — we patch the pool manually."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── GET /repos ────────────────────────────────────────────────────────────────

class TestListRepos:

    def test_returns_200_with_repos(self, client):
        pool_mock, conn_mock = _patch_fetch_repos([_make_mock_row()])
        with patch("app.db.client._pool", pool_mock):
            resp = client.get("/repos")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_repo_has_all_required_fields(self, client):
        pool_mock, conn_mock = _patch_fetch_repos([_make_mock_row()])
        with patch("app.db.client._pool", pool_mock):
            resp = client.get("/repos")
        repo = resp.json()[0]
        assert "id" in repo
        assert "score" in repo
        assert "tier" in repo
        assert "score_breakdown" in repo
        assert "complexity_estimate" in repo
        assert "unavailable_metrics" in repo
        assert "topics" in repo

    def test_score_breakdown_uses_welcome_pillar(self, client):
        pool_mock, _ = _patch_fetch_repos([_make_mock_row()])
        with patch("app.db.client._pool", pool_mock):
            resp = client.get("/repos")
        bd = resp.json()[0]["score_breakdown"]
        assert "welcome" in bd
        assert "beginner" not in bd

    def test_topics_is_list(self, client):
        pool_mock, _ = _patch_fetch_repos([_make_mock_row(topics=["python", "flask"])])
        with patch("app.db.client._pool", pool_mock):
            resp = client.get("/repos")
        assert resp.json()[0]["topics"] == ["python", "flask"]

    def test_unavailable_metrics_is_list(self, client):
        pool_mock, _ = _patch_fetch_repos(
            [_make_mock_row(unavailable_metrics=["pull_requests_30d"])]
        )
        with patch("app.db.client._pool", pool_mock):
            resp = client.get("/repos")
        assert resp.json()[0]["unavailable_metrics"] == ["pull_requests_30d"]

    def test_empty_result_returns_empty_list(self, client):
        pool_mock, _ = _patch_fetch_repos([])
        with patch("app.db.client._pool", pool_mock):
            resp = client.get("/repos")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_invalid_tier_returns_422(self, client):
        resp = client.get("/repos?tier=invalid_tier")
        assert resp.status_code == 422

    def test_min_score_out_of_range_returns_422(self, client):
        resp = client.get("/repos?min_score=999")
        assert resp.status_code == 422

    def test_limit_too_large_returns_422(self, client):
        resp = client.get("/repos?limit=999")
        assert resp.status_code == 422

    def test_multiple_repos_returned(self, client):
        rows = [_make_mock_row(repo_id=REPO_UUID), _make_mock_row(repo_id=REPO_UUID_2)]
        pool_mock, _ = _patch_fetch_repos(rows)
        with patch("app.db.client._pool", pool_mock):
            resp = client.get("/repos")
        assert len(resp.json()) == 2

    def test_tier_none_allowed_in_response(self, client):
        """Repos below quality floor have tier=None."""
        pool_mock, _ = _patch_fetch_repos([_make_mock_row(tier=None)])
        with patch("app.db.client._pool", pool_mock):
            resp = client.get("/repos")
        assert resp.json()[0]["tier"] is None


# ── GET /repos/{repo_id} ──────────────────────────────────────────────────────

class TestGetRepo:

    def test_returns_200_for_existing_repo(self, client):
        pool_mock, _ = _patch_fetch_repo(_make_mock_row())
        with patch("app.db.client._pool", pool_mock):
            resp = client.get(f"/repos/{REPO_UUID}")
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "pallets/flask"

    def test_returns_404_for_missing_repo(self, client):
        conn_mock = AsyncMock()
        conn_mock.fetchrow = AsyncMock(return_value=None)
        pool_mock = MagicMock()
        pool_mock.acquire = MagicMock(return_value=_async_ctx(conn_mock))
        with patch("app.db.client._pool", pool_mock):
            resp = client.get(f"/repos/{REPO_UUID}")
        assert resp.status_code == 404

    def test_malformed_uuid_returns_422(self, client):
        resp = client.get("/repos/not-a-uuid")
        assert resp.status_code == 422

    def test_single_repo_has_complexity_estimate(self, client):
        pool_mock, _ = _patch_fetch_repo(_make_mock_row(complexity_estimate=55.2))
        with patch("app.db.client._pool", pool_mock):
            resp = client.get(f"/repos/{REPO_UUID}")
        assert resp.json()["complexity_estimate"] == 55.2

    def test_single_repo_score_breakdown_welcome_field(self, client):
        pool_mock, _ = _patch_fetch_repo(_make_mock_row())
        with patch("app.db.client._pool", pool_mock):
            resp = client.get(f"/repos/{REPO_UUID}")
        bd = resp.json()["score_breakdown"]
        assert "welcome" in bd
        assert "beginner" not in bd
