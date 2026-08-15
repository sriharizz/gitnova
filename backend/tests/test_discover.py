"""
GitNova v4.2 — Discovery Unit Tests

Tests for discovery allocation algorithm (_balanced_select).
Ensures query pools receive fair representation, early pools do not dominate,
and unused slots are redistributed properly.

Run: pytest tests/test_discover.py -v
"""

import pytest
from app.intelligence.discover import _balanced_select, _build_queries


def test_balanced_select_equal_distribution():
    pools = {
        0: [f"python/repo{i}" for i in range(20)],
        1: [f"js/repo{i}" for i in range(20)],
        2: [f"ts/repo{i}" for i in range(20)],
    }
    # Max candidates 30, 3 pools → fair share = 10 each
    result = _balanced_select(pools, max_candidates=30)
    assert len(result) == 30
    py_count = sum(1 for r in result if r.startswith("python/"))
    js_count = sum(1 for r in result if r.startswith("js/"))
    ts_count = sum(1 for r in result if r.startswith("ts/"))
    assert py_count == 10
    assert js_count == 10
    assert ts_count == 10


def test_balanced_select_redistributes_unused_slots():
    pools = {
        0: ["python/repo1", "python/repo2"],  # Only 2 candidates (fair share is 10)
        1: [f"js/repo{i}" for i in range(20)],
        2: [f"ts/repo{i}" for i in range(20)],
    }
    # Max candidates 30, 3 pools → initial fair share = 10. Pool 0 yields 2.
    # Unused 8 slots are redistributed to pools 1 and 2.
    result = _balanced_select(pools, max_candidates=30)
    assert len(result) == 30
    py_count = sum(1 for r in result if r.startswith("python/"))
    assert py_count == 2
    # Pools 1 and 2 get their initial 10 plus 4 extra each
    js_count = sum(1 for r in result if r.startswith("js/"))
    ts_count = sum(1 for r in result if r.startswith("ts/"))
    assert js_count == 14
    assert ts_count == 14


def test_balanced_select_stops_when_pools_exhausted():
    pools = {
        0: ["python/repo1"],
        1: ["js/repo1"],
    }
    result = _balanced_select(pools, max_candidates=100)
    assert len(result) == 2
    assert result == ["python/repo1", "js/repo1"]


def test_balanced_select_empty_pools():
    pools = {0: [], 1: []}
    result = _balanced_select(pools, max_candidates=50)
    assert result == []


def test_build_queries_generates_all_queries():
    config = {
        "min_stars": 50,
        "activity_window_days": 90,
        "languages": ["python", "javascript", "rust"],
        "cross_language_queries": [
            "stars:>{min_stars} pushed:>{cutoff_date} topic:library"
        ]
    }
    queries = _build_queries(config)
    assert len(queries) == 4
    assert "language:python" in queries[0]
    assert "language:javascript" in queries[1]
    assert "language:rust" in queries[2]
    assert "topic:library" in queries[3]
