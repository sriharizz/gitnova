"""
GitNova v4.2 — Sprint 8 Hybrid Retrieval Unit & Scoping Tests

Tests for:
  - Repository isolation (repo_id / target_repo matching)
  - ACTIVE snapshot isolation
  - Reciprocal Rank Fusion (RRF) determinism (k=60)
  - Metadata preservation (info_class, qualified_symbol_name, contextual_header)
  - Content deduplication & file concentration guard (max 3 chunks / file)
  - Token budget enforcement (max_tokens ceiling)
"""

from unittest.mock import MagicMock
from uuid import UUID
import pytest

from app.pipeline.code_retriever import (
    rrf_score,
    combine_rrf,
    retrieve_code_for_issue,
)


# ── RRF Determinism & Math Tests ─────────────────────────────────────────────

class TestRRFScore:

    def test_rrf_score_single_rank(self):
        score = rrf_score([1], k=60)
        assert score == pytest.approx(1.0 / 61.0)

    def test_rrf_score_multiple_ranks(self):
        score = rrf_score([1, 2], k=60)
        assert score == pytest.approx((1.0 / 61.0) + (1.0 / 62.0))

    def test_combine_rrf_boosts_overlapping_candidates(self):
        vec = [
            {"chunk_id": "c1", "file_path": "a.py", "start_line": 1, "end_line": 10, "content": "def f(): pass", "info_class": "SOURCE_CODE", "contextual_header": "[File: a.py]"},
            {"chunk_id": "c2", "file_path": "b.py", "start_line": 1, "end_line": 10, "content": "def g(): pass", "info_class": "SOURCE_CODE", "contextual_header": "[File: b.py]"},
        ]
        lex = [
            {"chunk_id": "c2", "file_path": "b.py", "start_line": 1, "end_line": 10, "content": "def g(): pass", "info_class": "SOURCE_CODE", "contextual_header": "[File: b.py]"},
            {"chunk_id": "c3", "file_path": "c.py", "start_line": 1, "end_line": 10, "content": "def h(): pass", "info_class": "SOURCE_CODE", "contextual_header": "[File: c.py]"},
        ]

        fused = combine_rrf(vec, lex, k=60)

        # c2 was present in BOTH lists -> should rank #1
        assert fused[0]["chunk_id"] == "c2"
        assert fused[0]["rrf_score"] > fused[1]["rrf_score"]

    def test_combine_rrf_preserves_sprint_6_7_metadata(self):
        vec = [{
            "chunk_id": "c1",
            "file_path": "src/auth.py",
            "symbol_name": "login",
            "qualified_symbol_name": "AuthManager.login",
            "symbol_type": "method",
            "info_class": "SOURCE_CODE",
            "contextual_header": "[File: src/auth.py | Class: AuthManager | Method: login (Lines 1-10)]",
            "start_line": 1,
            "end_line": 10,
            "content": "def login(): pass",
            "repo_id": "00000000-0000-0000-0000-000000000001",
        }]

        fused = combine_rrf(vec, [], k=60)
        assert fused[0]["qualified_symbol_name"] == "AuthManager.login"
        assert fused[0]["info_class"] == "SOURCE_CODE"
        assert fused[0]["contextual_header"].startswith("[File: src/auth.py")


# ── Context Formatting, Concentration Guard & Token Budget Tests ──────────────

class TestRetrieverContextFormatting:

    def test_retrieve_code_uses_contextual_header(self):
        supabase_mock = MagicMock()
        supabase_mock.rpc().execute.return_value.data = [{
            "chunk_id": "c1",
            "file_path": "src/app.py",
            "symbol_name": "main",
            "start_line": 1,
            "end_line": 5,
            "content": "def main(): pass",
            "contextual_header": "[File: src/app.py | Function: main (Lines 1-5)]",
        }]

        context, chunk_ids = retrieve_code_for_issue(
            supabase_client=supabase_mock,
            repo_name="pallets/flask",
            commit_sha="sha123",
            issue_title="Test Issue",
            issue_body="Bug in main",
            mode="vector_only",
        )

        assert "--- [File: src/app.py | Function: main (Lines 1-5)] ---" in context
        assert "def main(): pass" in context
        assert chunk_ids == ["c1"]

    def test_file_concentration_guard_caps_at_3_chunks_per_file(self):
        chunks = [
            {"chunk_id": f"c{i}", "file_path": "src/large.py", "start_line": i*10, "end_line": i*10+9, "content": f"code_block_{i}", "contextual_header": f"[Chunk {i}]"}
            for i in range(5)
        ]

        supabase_mock = MagicMock()
        supabase_mock.rpc().execute.return_value.data = chunks

        context, chunk_ids = retrieve_code_for_issue(
            supabase_client=supabase_mock,
            repo_name="pallets/flask",
            commit_sha="sha123",
            issue_title="Test Issue",
            issue_body="Bug",
            mode="vector_only",
        )

        # Max 3 chunks from src/large.py allowed
        assert len(chunk_ids) == 3
        assert chunk_ids == ["c0", "c1", "c2"]

    def test_token_budget_enforcement(self):
        long_content = "word " * 500  # ~650 estimated tokens
        chunks = [
            {"chunk_id": f"c{i}", "file_path": f"src/file_{i}.py", "start_line": 1, "end_line": 10, "content": long_content, "contextual_header": f"[File {i}]"}
            for i in range(5)
        ]

        supabase_mock = MagicMock()
        supabase_mock.rpc().execute.return_value.data = chunks

        # Budget cap = 1000 tokens -> should fit only ~1-2 chunks
        context, chunk_ids = retrieve_code_for_issue(
            supabase_client=supabase_mock,
            repo_name="pallets/flask",
            commit_sha="sha123",
            issue_title="Test Issue",
            issue_body="Bug",
            max_tokens=1000,
            mode="vector_only",
        )

        assert len(chunk_ids) <= 2


# ── Information-Class Weighting Regression Tests ──────────────────────────────

class TestInformationClassWeighting:

    def test_information_class_weighting_promotes_source_code_over_docs(self):
        # Doc chunk at rank 1 (raw RRF = 1/61 = 0.01639)
        # Source chunk at rank 2 (raw RRF = 1/62 = 0.016129)
        vec = [
            {"chunk_id": "doc1", "file_path": "README.md", "start_line": 1, "end_line": 20, "content": "How to start cli", "info_class": "DOCUMENTATION"},
            {"chunk_id": "src1", "file_path": "start.js", "start_line": 1, "end_line": 20, "content": "function start() {}", "info_class": "SOURCE_CODE"},
        ]

        # Raw combine_rrf with default weights
        fused = combine_rrf(vec, [], k=60)

        # Post-RRF weighting: src1 gets 1.10 multiplier (0.016129 * 1.10 = 0.01774)
        # doc1 gets 1.00 multiplier (0.01639 * 1.00 = 0.01639)
        # src1 should now rank #1
        assert fused[0]["chunk_id"] == "src1"
        assert fused[0]["info_class"] == "SOURCE_CODE"
        assert fused[1]["chunk_id"] == "doc1"

    def test_documentation_only_results_remain_documentation(self):
        vec = [
            {"chunk_id": "doc1", "file_path": "docs/guide.md", "start_line": 1, "end_line": 20, "content": "User guide", "info_class": "DOCUMENTATION"},
            {"chunk_id": "doc2", "file_path": "docs/api.md", "start_line": 1, "end_line": 20, "content": "API guide", "info_class": "DOCUMENTATION"},
        ]

        fused = combine_rrf(vec, [], k=60)
        assert fused[0]["chunk_id"] == "doc1"
        assert fused[0]["info_class"] == "DOCUMENTATION"
        assert fused[1]["chunk_id"] == "doc2"

    def test_tests_are_retrievable_but_penalized_relative_to_source(self):
        # Test chunk at rank 1 (raw RRF = 1/61 = 0.01639, weighted = 0.01639 * 0.90 = 0.01475)
        # Source chunk at rank 2 (raw RRF = 1/62 = 0.016129, weighted = 0.016129 * 1.10 = 0.01774)
        vec = [
            {"chunk_id": "test1", "file_path": "test/app_test.py", "start_line": 1, "end_line": 20, "content": "def test_app(): pass", "info_class": "TESTS"},
            {"chunk_id": "src1", "file_path": "src/app.py", "start_line": 1, "end_line": 20, "content": "def app(): pass", "info_class": "SOURCE_CODE"},
        ]

        fused = combine_rrf(vec, [], k=60)
        # src1 should outrank test1
        assert fused[0]["chunk_id"] == "src1"
        assert fused[0]["info_class"] == "SOURCE_CODE"
        # test1 must NOT be removed; it remains retrievable at rank #2
        assert fused[1]["chunk_id"] == "test1"
        assert fused[1]["info_class"] == "TESTS"

    def test_configuration_remains_retrievable_and_unaffected(self):
        vec = [
            {"chunk_id": "cfg1", "file_path": "package.json", "start_line": 1, "end_line": 50, "content": "{\"name\": \"app\"}", "info_class": "CONFIGURATION"},
            {"chunk_id": "doc1", "file_path": "README.md", "start_line": 1, "end_line": 20, "content": "Readme text", "info_class": "DOCUMENTATION"},
        ]

        fused = combine_rrf(vec, [], k=60)
        assert fused[0]["chunk_id"] == "cfg1"
        assert fused[0]["info_class"] == "CONFIGURATION"
        assert fused[1]["chunk_id"] == "doc1"

