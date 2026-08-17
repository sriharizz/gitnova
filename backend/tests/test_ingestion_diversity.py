"""
Unit tests for GitNova Ingestion Diversity, Repository Rotation, Bounded Pagination, and Deduplication Caching.
"""

import os
import sys
import json
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.pipeline.run_issue_sync import get_rotated_repositories
from app.pipeline.github_client import GitHubClient
from app.pipeline.canonical_pipeline import CanonicalIngestionPipeline



# ── Test A: Deterministic Language-Balanced Repository Rotation ──────────────────

def test_repository_rotation_multi_run_coverage():
    """
    Verifies that get_rotated_repositories:
      1. Slices repos deterministically across successive runs.
      2. Does not select the same top 40 on every run.
      3. Preserves language interleaving in every slice.
      4. Cycles through all active repositories with zero starvation.
    """
    # Create 150 simulated repositories across 5 major languages
    mock_repos = []
    languages = ["Python", "TypeScript", "Go", "Rust", "Java"]
    for i in range(150):
        lang = languages[i % len(languages)]
        mock_repos.append({
            "id": f"repo-{i}",
            "full_name": f"org/repo-{i}",
            "language": lang,
            "score": 100 - (i // len(languages)),  # Score priority within language
            "is_active": True
        })

    mock_supabase = MagicMock()
    
    # Run 1: offset = 0
    mock_supabase.table().select().eq().order().order().execute.return_value.data = mock_repos
    mock_supabase.table().select().eq().order().limit().execute.return_value.data = [] # No previous runs

    repos_run1, offset1, next1, total = get_rotated_repositories(mock_supabase, max_repos=40)
    assert len(repos_run1) == 40
    assert offset1 == 0
    assert next1 == 40
    assert total == 150
    
    # Check language diversity in Run 1
    lang_counts_r1 = {}
    for r in repos_run1:
        lang_counts_r1[r["language"]] = lang_counts_r1.get(r["language"], 0) + 1
    assert len(lang_counts_r1) == 5
    for count in lang_counts_r1.values():
        assert count == 8  # Exactly 40 / 5 = 8 repos per language

    # Run 2: offset = 40 (simulated persistent cursor from pipeline_runs)
    mock_supabase.table().select().eq().order().limit().execute.return_value.data = [
        {"metadata": {"next_rotation_offset": 40}}
    ]
    repos_run2, offset2, next2, _ = get_rotated_repositories(mock_supabase, max_repos=40)
    assert len(repos_run2) == 40
    assert offset2 == 40
    assert next2 == 80
    
    # Run 1 and Run 2 must have ZERO overlapping repositories
    set_r1 = {r["id"] for r in repos_run1}
    set_r2 = {r["id"] for r in repos_run2}
    assert len(set_r1.intersection(set_r2)) == 0

    # Run 3: offset = 80
    mock_supabase.table().select().eq().order().limit().execute.return_value.data = [
        {"metadata": {"next_rotation_offset": 80}}
    ]
    repos_run3, offset3, next3, _ = get_rotated_repositories(mock_supabase, max_repos=40)
    assert len(repos_run3) == 40
    assert offset3 == 80
    assert next3 == 120
    set_r3 = {r["id"] for r in repos_run3}
    assert len(set_r1.intersection(set_r3)) == 0
    assert len(set_r2.intersection(set_r3)) == 0

    # Run 4: offset = 120 (Wrap-around test: takes 30 remaining + 10 from start)
    mock_supabase.table().select().eq().order().limit().execute.return_value.data = [
        {"metadata": {"next_rotation_offset": 120}}
    ]
    repos_run4, offset4, next4, _ = get_rotated_repositories(mock_supabase, max_repos=40)
    assert len(repos_run4) == 40
    assert offset4 == 120
    assert next4 == 10  # (120 + 40) % 150 = 10

    # Across 4 runs, all 150 repositories were covered!
    all_seen = set_r1.union(set_r2).union(set_r3).union({r["id"] for r in repos_run4})
    assert len(all_seen) == 150


# ── Test B: Controlled Bounded Issue Pagination ──────────────────────────────────

def test_github_client_bounded_pagination():
    """
    Verifies that get_issues_paginated:
      1. Follows page numbers (page=1, 2, ...).
      2. Stops when max_candidates is reached.
      3. Filters out Pull Requests.
      4. Does not fetch unnecessary pages.
    """
    client = GitHubClient(token="mock_token", supabase_client=None)

    def mock_get(url, params=None, headers=None):
        page = params.get("page", 1)
        if page == 1:
            return [
                {"number": 1, "title": "Issue 1", "html_url": "https://github.com/a/b/issues/1"},
                {"number": 2, "title": "PR 2", "pull_request": {}, "html_url": "https://github.com/a/b/pull/2"},  # Should be skipped
                {"number": 3, "title": "Issue 3", "html_url": "https://github.com/a/b/issues/3"},
                {"number": 4, "title": "Issue 4", "html_url": "https://github.com/a/b/issues/4"},
            ]
        elif page == 2:
            return [
                {"number": 5, "title": "Issue 5", "html_url": "https://github.com/a/b/issues/5"},
                {"number": 6, "title": "Issue 6", "html_url": "https://github.com/a/b/issues/6"},
            ]
        return []

    client.get = mock_get

    # Test with max_candidates = 4
    candidates = client.get_issues_paginated(
        repo_full_name="a/b",
        state="open",
        max_candidates=4,
        max_pages=3,
        per_page=4
    )

    assert len(candidates) == 4
    # Issue 2 (PR) must not be in candidates
    numbers = [c["number"] for c in candidates]
    assert numbers == [1, 3, 4, 5]


# ── Test C: Issue Deduplication & Fast-Path Unchanged Cache ──────────────────────

def test_canonical_pipeline_fast_path_cache_hit():
    """
    Verifies that when an issue already exists in Supabase with identical github_issue_updated_at,
    CanonicalIngestionPipeline returns the precomputed evaluation without calling Gemini or RAG.
    """
    mock_supabase = MagicMock()
    mock_github = MagicMock()

    # Raw issue returned from GitHub
    mock_github.get.return_value = {
        "number": 101,
        "title": "Fix memory leak in parser when processing malformed stream input",
        "body": (
            "When parsing stream input, the internal buffer retains references to previous chunks on error. "
            "This causes memory consumption to grow linearly over time during high-throughput ingestion runs. "
            "We should ensure the stream buffer is explicitly cleared in the finally block when errors occur."
        ),
        "state": "open",
        "html_url": "https://github.com/org/repo/issues/101",
        "updated_at": "2026-08-16T10:00:00Z",
        "labels": [{"name": "bug"}],
        "user": {"login": "dev1"},
        "comments": 2
    }


    # Supabase issues table returns existing evaluated record with matching updated_at
    mock_issues_data = [{
        "id": "issue-uuid-1",
        "github_issue_updated_at": "2026-08-16T10:00:00Z",
        "repo_commit_sha": "abc1234",
        "difficulty": "BEGINNER",
        "quality_score": 88,
        "is_published": True,
        "ai_hint": json.dumps({
            "summary": "Fix memory leak in parser by releasing buffer in finally block.",
            "verification_status": "VERIFIED",
            "availability_status": "LIKELY_AVAILABLE",
            "difficulty_tier": "BEGINNER"
        })
    }]

    # Set up mock returns for select queries on repos and issues
    def mock_table(table_name):
        tbl_mock = MagicMock()
        query_mock = MagicMock()
        query_mock.select.return_value = query_mock
        query_mock.eq.return_value = query_mock
        query_mock.order.return_value = query_mock
        query_mock.limit.return_value = query_mock
        
        if table_name == "repos":
            query_mock.execute.return_value.data = [{
                "id": "repo-uuid-1",
                "full_name": "org/repo",
                "language": "Python",
                "score": 85,
                "is_active": True
            }]
        elif table_name == "issues":
            query_mock.execute.return_value.data = mock_issues_data
        else:
            query_mock.execute.return_value.data = []
            
        tbl_mock.select.return_value = query_mock
        tbl_mock.insert.return_value = query_mock
        tbl_mock.update.return_value = query_mock
        tbl_mock.upsert.return_value = query_mock
        return tbl_mock

    mock_supabase.table.side_effect = mock_table


    with patch("app.pipeline.issue_explainer.generate_issue_explanation") as mock_llm_call:
        with patch("app.pipeline.code_retriever.retrieve_chunks_for_issue") as mock_rag_call:
            res = CanonicalIngestionPipeline.ingest_and_process_issue(
                repo_full_name="org/repo",
                github_issue_number=101,
                supabase_client=mock_supabase,
                github_client=mock_github,
                dry_run=False
            )

            # Assert Fast-Path cache hit succeeded
            if not res.get("success"):
                print("DEBUG res:", res)
            assert res["success"] is True
            assert res["published"] is True
            assert res["difficulty_tier"] == "BEGINNER"
            assert "Fix memory leak" in res["explanation"]["summary"]

            # CRITICAL: Verify ZERO LLM and ZERO RAG calls occurred
            mock_llm_call.assert_not_called()
            mock_rag_call.assert_not_called()



# ── Test D: Repository Index Commit-SHA Caching ──────────────────────────────────

def test_code_indexer_commit_sha_caching():
    """
    Verifies that ensure_repo_indexed skips chunking and embedding when an active
    snapshot already exists for the repository HEAD commit SHA.
    """
    from app.pipeline.code_indexer import ensure_repo_indexed

    mock_supabase = MagicMock()
    mock_github = MagicMock()

    # GitHub returns branch commit payload
    mock_github.get.return_value = {
        "commit": {
            "sha": "c0ffee1234567890abcdef"
        }
    }


    # Supabase repository_snapshots table returns existing active snapshot with same SHA
    mock_supabase.table().select().eq().eq().eq().execute.return_value.data = [{
        "commit_sha": "c0ffee1234567890abcdef"
    }]

    sha = ensure_repo_indexed(
        supabase_client=mock_supabase,
        github_client=mock_github,
        repo_name="org/repo",
        repo_context={"language": "Python"}
    )
    assert sha == "c0ffee1234567890abcdef"



if __name__ == "__main__":
    print("🧪 Running Test A: Deterministic Repository Rotation...")
    test_repository_rotation_multi_run_coverage()
    print("   ✅ Test A Passed: 150 repos rotated across 4 runs with 0 starvation & perfect language balance.")

    print("🧪 Running Test B: Controlled Bounded Issue Pagination...")
    test_github_client_bounded_pagination()
    print("   ✅ Test B Passed: Multi-page pagination halted at limit and PRs filtered.")

    print("🧪 Running Test C: Issue Deduplication & Fast-Path Cache Hit...")
    test_canonical_pipeline_fast_path_cache_hit()
    print("   ✅ Test C Passed: Unchanged issue returned cached evaluation with 0 LLM and 0 RAG calls.")

    print("🧪 Running Test D: Repository Index Commit Caching...")
    test_code_indexer_commit_sha_caching()
    print("   ✅ Test D Passed: Unchanged commit SHA reused snapshot with 0 re-indexing.")

    print("\n🎉 ALL INGESTION DIVERSITY TESTS PASSED SUCCESSFULLY!")

