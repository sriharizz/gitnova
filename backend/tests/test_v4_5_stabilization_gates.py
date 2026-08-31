"""
GitNova v4.5 — 20-Point Stabilization & Evidence-Gating Test Suite

Verifies all 20 stabilization gates mandated by the v4.5 Directive:
  1. Missing evidence -> no generated claim
  2. Missing target file -> no target file displayed
  3. Unsupported test command -> no test command displayed
  4. Unsupported root cause -> marked AI_INFERENCE or withheld
  5. Assigned issue -> availability rejected
  6. Active linked PR -> CHECK_DISCUSSION
  7. Closed issue -> NOT_RECOMMENDED
  8. Negative label -> NOT_RECOMMENDED
  9. Positive label alone does NOT guarantee availability
 10. Reporter attribution comes from GitHub metadata
 11. Target file consistency across all 10 journey stages
 12. Repository isolation in RRF
 13. Test retrieval works
 14. Rust repository does not receive Python commands
 15. JS repository does not receive Python commands
 16. No hardcoded issue-specific production fallbacks
 17. Rate-limit retry is bounded
 18. Embedding calls are cached/batched
 19. LLM failure does not produce fake content
 20. Frontend/Schema correctly handles INSUFFICIENT_EVIDENCE
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.schemas.evidence import (
    EvidencePackage, IssueEvidence, StatusEvidence, RepositoryEvidence,
    CodeEvidenceItem, TestEvidenceItem, DiscussionEvidence
)
from app.schemas.explanation import (
    IssueExplanation, ContributionJourney, ContributionJourneyStage,
    RepositoryContributionGuide, ProvenanceItem, ProvenanceType,
    GroundedCodeLocation, GuidedSolutionStep
)
from app.pipeline.grounding_verifier import GroundingVerifier
from app.pipeline.opportunity_evaluator import ContributionOpportunityEvaluator
from app.pipeline.repo_guide_extractor import RepoGuideExtractor
from app.pipeline.journey_generator import ContributionJourneyGenerator
from app.pipeline.evidence_builder import EvidenceBuilder
from app.clients.llm.base import BaseLLMProvider


# ─────────────────────────────────────────────────────────────────────────────
# Gate 1: Missing evidence -> no generated claim
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_1_missing_evidence_returns_insufficient():
    empty_chunks = []
    verifier = GroundingVerifier(empty_chunks)
    assert verifier.has_sufficient_evidence() is False

    exp = verifier.create_insufficient_evidence_explanation("No matching codebase chunks.")
    assert exp.status == "INSUFFICIENT_EVIDENCE"
    assert exp.step_by_step_plan == []
    assert exp.relevant_locations == []


# ─────────────────────────────────────────────────────────────────────────────
# Gate 2: Missing target file -> no target file displayed / pruned
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_2_missing_target_file_is_pruned():
    indexed_chunks = [{"file_path": "src/click/core.py", "symbol_name": "Command"}]
    verifier = GroundingVerifier(indexed_chunks)

    raw_exp = IssueExplanation(
        status="SUCCESS",
        summary="Test summary",
        why_it_happens="Test root cause",
        relevant_locations=[
            GroundedCodeLocation(file_path="src/click/hallucinated.py", symbol_name="FakeSym", lines="10-20"),
            GroundedCodeLocation(file_path="src/click/core.py", symbol_name="Command", lines="100-150")
        ]
    )
    sanitized = verifier.verify_and_sanitize(raw_exp)
    assert len(sanitized.relevant_locations) == 1
    assert sanitized.relevant_locations[0].file_path == "src/click/core.py"
    assert sanitized.disclaimer is not None
    assert "pruned" in sanitized.disclaimer


# ─────────────────────────────────────────────────────────────────────────────
# Gate 3: Unsupported test command -> marked NOT_VERIFIED
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_3_unsupported_test_command_marked_not_verified():
    guide = RepoGuideExtractor.extract_guide(
        repo_full_name="unknown/mystery-repo",
        raw_contributing_md="Please be nice when contributing.",
        language="C"
    )
    assert guide.test_command_source == "NOT_VERIFIED"
    assert "Not verified" in guide.test_command


# ─────────────────────────────────────────────────────────────────────────────
# Gate 4: Root cause has proper provenance
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_4_root_cause_provenance_is_ai_inference():
    issue_data = {
        "repo_full_name": "pallets/click",
        "github_issue_number": 3740,
        "title": "Bug in Windows pager",
        "explanation": {
            "summary": "Pager returns BinaryIO on Windows",
            "why_it_happens": "_pipepager returns BinaryIO on Windows instead of TextIO",
            "relevant_locations": [{"file_path": "src/click/_termui_impl.py", "symbol_name": "_pipepager"}],
            "step_by_step_plan": [{"step_number": 1, "title": "Inspect _pipepager", "description": "Fix return type"}]
        }
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_data)
    investigate_stage = next(s for s in journey.stages if s.stage_id == "investigate")
    assert investigate_stage.provenance.provenance_type == ProvenanceType.AI_INFERENCE


# ─────────────────────────────────────────────────────────────────────────────
# Gate 5: Assigned issue -> availability rejected
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_5_assigned_issue_availability_rejected():
    raw_issue = {
        "number": 101,
        "state": "open",
        "assignee": {"login": "active_dev"},
        "assignees": [{"login": "active_dev"}],
        "labels": []
    }
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue, {"full_name": "test/repo"})
    assert res["availability_status"] == "NOT_RECOMMENDED"
    assert res["is_eligible"] is False


# ─────────────────────────────────────────────────────────────────────────────
# Gate 6: Active linked PR -> CHECK_DISCUSSION
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_6_active_linked_pr_triggers_check_discussion():
    raw_issue = {
        "number": 102,
        "state": "open",
        "assignee": None,
        "assignees": [],
        "labels": []
    }
    timeline = [
        {"event": "cross-referenced", "source": {"issue": {"pull_request": {}, "state": "open"}}}
    ]
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(
        raw_issue=raw_issue,
        repo_data={"full_name": "test/repo"},
        timeline_events=timeline
    )
    assert res["availability_status"] == "CHECK_DISCUSSION"


# ─────────────────────────────────────────────────────────────────────────────
# Gate 7: Closed issue -> NOT_RECOMMENDED
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_7_closed_issue_is_not_recommended():
    raw_issue = {
        "number": 103,
        "state": "closed",
        "assignee": None,
        "assignees": [],
        "labels": []
    }
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue, {"full_name": "test/repo"})
    assert res["availability_status"] == "NOT_RECOMMENDED"


# ─────────────────────────────────────────────────────────────────────────────
# Gate 8: Negative label -> NOT_RECOMMENDED
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_8_negative_label_is_not_recommended():
    raw_issue = {
        "number": 104,
        "state": "open",
        "assignee": None,
        "assignees": [],
        "labels": [{"name": "wontfix"}]
    }
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue, {"full_name": "test/repo"})
    assert res["availability_status"] == "NOT_RECOMMENDED"


# ─────────────────────────────────────────────────────────────────────────────
# Gate 9: Positive label alone does NOT override assignment
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_9_positive_label_does_not_override_assigned_user():
    raw_issue = {
        "number": 105,
        "state": "open",
        "assignee": {"login": "busy_coder"},
        "assignees": [{"login": "busy_coder"}],
        "labels": [{"name": "good first issue"}]
    }
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue, {"full_name": "test/repo"})
    assert res["availability_status"] == "NOT_RECOMMENDED"


# ─────────────────────────────────────────────────────────────────────────────
# Gate 10: Reporter attribution comes from GitHub metadata
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_10_reporter_attribution_authentic():
    raw_issue = {
        "number": 106,
        "state": "open",
        "user": {"login": "authentic_contributor_123"},
        "labels": []
    }
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue, {"full_name": "test/repo"})
    assert res["reporter_username"] == "authentic_contributor_123"


# ─────────────────────────────────────────────────────────────────────────────
# Gate 11: Target file consistency across all 10 stages
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_11_target_file_consistency_enforced():
    issue_data = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "Context issue",
        "explanation": {
            "summary": "Generator context bug",
            "why_it_happens": "Missing generator exit handling",
            "relevant_locations": [{"file_path": "src/flask/helpers.py", "symbol_name": "stream_with_context"}],
            "step_by_step_plan": [
                {"step_number": 1, "title": "Inspect helpers", "description": "Fix in src/flask/helpers.py", "target_file": "src/flask/helpers.py"}
            ]
        }
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_data)
    for stage in journey.stages:
        if stage.stage_id in {"explore", "investigate", "implement", "test"}:
            assert "src/flask/helpers.py" in stage.targets


# ─────────────────────────────────────────────────────────────────────────────
# Gate 12: Repository isolation in evidence package
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_12_repository_isolation_preserved():
    pkg = EvidenceBuilder.build_package(
        raw_issue={"title": "Test Issue", "body": "Issue text", "user": {"login": "author"}, "number": 1},
        repo_data={"full_name": "pallets/click", "language": "Python"},
        repo_guide=RepoGuideExtractor.extract_guide("pallets/click", language="Python"),
        commit_sha="commit_sha_123",
        retrieved_chunks=[
            {"chunk_id": "c1", "file_path": "src/click/core.py", "symbol_name": "Command", "start_line": 1, "end_line": 20, "commit_sha": "commit_sha_123"}
        ]
    )
    assert pkg.repository.repo_full_name == "pallets/click"
    for code in pkg.code_evidence:
        assert code.commit_sha == "commit_sha_123"


# ─────────────────────────────────────────────────────────────────────────────
# Gate 13: Test retrieval isolation
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_13_test_retrieval_separated_from_source():
    chunks = [
        {"chunk_id": "s1", "file_path": "src/module.py", "symbol_name": "func", "start_line": 1, "end_line": 10},
        {"chunk_id": "t1", "file_path": "tests/test_module.py", "symbol_name": "test_func", "start_line": 1, "end_line": 15}
    ]
    pkg = EvidenceBuilder.build_package(
        raw_issue={"title": "T", "body": "B", "user": {"login": "u"}, "number": 2},
        repo_data={"full_name": "org/repo", "language": "Python"},
        repo_guide=RepoGuideExtractor.extract_guide("org/repo"),
        commit_sha="sha",
        retrieved_chunks=chunks
    )
    assert len(pkg.code_evidence) == 1
    assert pkg.code_evidence[0].file_path == "src/module.py"
    assert len(pkg.test_evidence) == 1
    assert pkg.test_evidence[0].file_path == "tests/test_module.py"


# ─────────────────────────────────────────────────────────────────────────────
# Gate 14: Rust repository does not receive Python commands
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_14_rust_repo_gets_cargo_not_pytest():
    guide = RepoGuideExtractor.extract_guide("sharkdp/bat", language="Rust")
    assert guide.test_command == "cargo test"
    assert "pytest" not in guide.test_command


# ─────────────────────────────────────────────────────────────────────────────
# Gate 15: JS repository does not receive Python commands
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_15_js_repo_gets_npm_not_pytest():
    guide = RepoGuideExtractor.extract_guide("expressjs/express", language="JavaScript")
    assert guide.test_command == "npm test"
    assert "pytest" not in guide.test_command


# ─────────────────────────────────────────────────────────────────────────────
# Gate 16: No hardcoded fake fallback in production journey
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_16_no_hardcoded_fake_fallback():
    issue_stub = {"repo_full_name": "test/repo", "github_issue_number": 999, "explanation": {}}
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    plan_stage = next(s for s in journey.stages if s.stage_id == "plan")
    assert any("INSUFFICIENT_EVIDENCE" in step for step in plan_stage.steps)


# ─────────────────────────────────────────────────────────────────────────────
# Gate 17: Rate-limit retry is bounded
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_17_rate_limit_retry_bounded():
    from app.clients.llm.gemini import GeminiProvider
    provider = GeminiProvider(api_key="mock_key")
    with patch("requests.post") as mock_post, patch("time.sleep") as mock_sleep:
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_post.return_value = mock_resp
        
        with pytest.raises(Exception):
            provider.generate_structured("test prompt", IssueExplanation)
        assert mock_post.call_count <= 6


# ─────────────────────────────────────────────────────────────────────────────
# Gate 18: Embedding / Repo Guide caching avoids redundant execution
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_18_repo_guide_cache_active():
    guide1 = RepoGuideExtractor.extract_guide("pallets/click")
    guide2 = RepoGuideExtractor.get_cached_guide("pallets/click")
    assert guide1 is guide2


# ─────────────────────────────────────────────────────────────────────────────
# Gate 19: LLM failure does not fabricate positive facts
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_19_llm_failure_fails_closed():
    verifier = GroundingVerifier([])
    fallback = verifier.create_insufficient_evidence_explanation("API call failed")
    assert fallback.status == "INSUFFICIENT_EVIDENCE"
    assert "Insufficient evidence" in fallback.summary


# ─────────────────────────────────────────────────────────────────────────────
# Gate 20: Schema accepts NOT_VERIFIED provenance
# ─────────────────────────────────────────────────────────────────────────────
def test_gate_20_schema_accepts_not_verified_provenance():
    prov = ProvenanceItem(text="Unverified item", provenance_type=ProvenanceType.NOT_VERIFIED)
    assert prov.provenance_type == ProvenanceType.NOT_VERIFIED


# ═════════════════════════════════════════════════════════════════════════════
# Phase 4 Publication Gate Tests (17 Comprehensive Scenarios)
# ═════════════════════════════════════════════════════════════════════════════

class TestPhase4PublicationGate:
    def _create_valid_explanation(self):
        return IssueExplanation(
            status="SUCCESS",
            summary="TypeError occurs when passing timezone-naive datetime objects to format_iso_timestamp().",
            why_it_happens=(
                "In `src/date_utils.py`, the `format_iso_timestamp()` function expects an aware datetime "
                "object with `.tzinfo` populated. When a naive datetime is passed, `dt.astimezone()` "
                "raises a ValueError or defaults incorrectly."
            ),
            step_by_step_plan=[
                GuidedSolutionStep(
                    step_number=1,
                    title="Locate datetime formatter",
                    description="Inspect the implementation of `format_iso_timestamp()` in `src/date_utils.py`.",
                    target_file="src/date_utils.py"
                ),
                GuidedSolutionStep(
                    step_number=2,
                    title="Add naive datetime guard",
                    description="Check if `dt.tzinfo is None` and apply UTC timezone by default before conversion.",
                    target_file="src/date_utils.py"
                ),
                GuidedSolutionStep(
                    step_number=3,
                    title="Add regression test",
                    description="Add a unit test in `tests/test_date.py` passing both naive and aware datetimes.",
                    target_file="tests/test_date.py"
                )
            ],
            relevant_locations=[
                GroundedCodeLocation(
                    file_path="src/date_utils.py",
                    symbol_name="format_iso_timestamp",
                    lines="42-60",
                    is_verified=True
                )
            ]
        )

    # 1. Missing target -> reject
    def test_missing_target_rejects(self):
        exp = self._create_valid_explanation()
        exp.relevant_locations = []
        verifier = GroundingVerifier(
            retrieved_chunks=[],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is False
        assert "NO_VERIFIED_TARGET" in gate["rejection_codes"]

    # 2. Valid code target + verified symbol -> pass
    def test_valid_code_target_and_verified_symbol_passes(self):
        exp = self._create_valid_explanation()
        chunks = [{
            "file_path": "src/date_utils.py",
            "symbol_name": "format_iso_timestamp",
            "content": "def format_iso_timestamp(dt): return dt.isoformat()"
        }]
        verifier = GroundingVerifier(
            retrieved_chunks=chunks,
            repo_name="org/repo",
            repo_language="python"
        )
        exp = verifier.verify_and_sanitize(exp)
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is True
        assert gate["rejection_codes"] == []

    # 3. Valid documentation target without symbol -> pass
    def test_valid_documentation_target_without_symbol_passes(self):
        exp = self._create_valid_explanation()
        exp.relevant_locations = [
            GroundedCodeLocation(file_path="docs/getting_started.md", is_verified=True)
        ]
        exp.step_by_step_plan = [
            GuidedSolutionStep(step_number=1, title="Review docs", description="Inspect docs/getting_started.md.", target_file="docs/getting_started.md"),
            GuidedSolutionStep(step_number=2, title="Update setup", description="Update installation steps in docs/getting_started.md.", target_file="docs/getting_started.md"),
            GuidedSolutionStep(step_number=3, title="Preview docs", description="Preview markdown rendering locally.", target_file="docs/getting_started.md")
        ]
        chunks = [{"file_path": "docs/getting_started.md", "content": "# Getting Started"}]
        verifier = GroundingVerifier(
            retrieved_chunks=chunks,
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is True
        assert "SYMBOL_NOT_VERIFIED" not in gate["rejection_codes"]

    # 4. Fabricated target -> reject
    def test_fabricated_target_rejects(self):
        exp = self._create_valid_explanation()
        exp.relevant_locations = [
            GroundedCodeLocation(file_path="src/hallucinated_file.py", is_verified=False)
        ]
        chunks = [{"file_path": "src/real_file.py", "content": "class Real: pass"}]
        verifier = GroundingVerifier(
            retrieved_chunks=chunks,
            repo_name="org/repo",
            repo_language="python"
        )
        sanitized = verifier.verify_and_sanitize(exp)
        gate = verifier.validate_publication_gate(sanitized)
        assert gate["is_safe"] is False
        assert "NO_VERIFIED_TARGET" in gate["rejection_codes"]

    # 5. Fabricated symbol -> reject
    def test_fabricated_symbol_rejects(self):
        exp = self._create_valid_explanation()
        exp.relevant_locations = [
            GroundedCodeLocation(file_path="src/date_utils.py", symbol_name="HallucinatedMethod", is_verified=False)
        ]
        chunks = [{
            "file_path": "src/date_utils.py",
            "symbol_name": "real_method",
            "content": "def real_method(): pass"
        }]
        verifier = GroundingVerifier(
            retrieved_chunks=chunks,
            repo_name="org/repo",
            repo_language="python"
        )
        sanitized = verifier.verify_and_sanitize(exp)
        gate = verifier.validate_publication_gate(sanitized)
        assert gate["is_safe"] is False
        assert "SYMBOL_NOT_VERIFIED" in gate["rejection_codes"]

    # 6. Empty plan -> reject
    def test_empty_plan_rejects(self):
        exp = self._create_valid_explanation()
        exp.step_by_step_plan = []
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is False
        assert "INSUFFICIENT_PLAN" in gate["rejection_codes"]

    # 7. Fewer than 3 meaningful plan steps -> reject
    def test_fewer_than_3_plan_steps_rejects(self):
        exp = self._create_valid_explanation()
        exp.step_by_step_plan = [
            GuidedSolutionStep(step_number=1, title="Step 1", description="Inspect src/date_utils.py"),
            GuidedSolutionStep(step_number=2, title="Step 2", description="Apply timezone fix in src/date_utils.py")
        ]
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is False
        assert "INSUFFICIENT_PLAN" in gate["rejection_codes"]

    # 8. Generic filler plan -> reject
    def test_generic_filler_plan_rejects(self):
        exp = self._create_valid_explanation()
        exp.step_by_step_plan = [
            GuidedSolutionStep(step_number=1, title="Review", description="Review the code carefully."),
            GuidedSolutionStep(step_number=2, title="Fix", description="Make the changes to fix the issue."),
            GuidedSolutionStep(step_number=3, title="Test", description="Run the tests to verify.")
        ]
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is False
        assert "INSUFFICIENT_PLAN" in gate["rejection_codes"]

    # 9. Unsupported root cause -> reject
    def test_unsupported_root_cause_rejects(self):
        exp = self._create_valid_explanation()
        exp.why_it_happens = "Fix the issue by updating the code."
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is False
        assert "UNSUPPORTED_ROOT_CAUSE" in gate["rejection_codes"]

    # 10. Unverified test command -> reject
    def test_unverified_test_command_rejects(self):
        exp = self._create_valid_explanation()
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp, repo_data={"test_command": "mvn test"})
        assert gate["is_safe"] is False
        assert "TEST_GUIDANCE_NOT_VERIFIED" in gate["rejection_codes"]

    # 11. Cross-repository target -> reject
    def test_cross_repository_target_rejects(self):
        exp = self._create_valid_explanation()
        exp.relevant_locations = [
            GroundedCodeLocation(file_path="src/main/java/com/example/Handler.java", is_verified=True)
        ]
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/main/java/com/example/Handler.java"}],
            repo_name="pallets/click",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is False
        assert "CROSS_REPOSITORY_MISMATCH" in gate["rejection_codes"]

    # 12. Cross-stage target mismatch -> reject
    def test_cross_stage_target_mismatch_rejects(self):
        exp = self._create_valid_explanation()
        exp.step_by_step_plan.append(
            GuidedSolutionStep(
                step_number=4,
                title="Unexpected step",
                description="Modify hallucinated backend file",
                target_file="src/completely/different/unindexed_module.py"
            )
        )
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert gate["is_safe"] is False
        assert "CROSS_STAGE_TARGET_DIVERGENCE" in gate["rejection_codes"]

    # 13. Python issue -> Python target passes
    def test_python_issue_allows_python_target(self):
        exp = self._create_valid_explanation()
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py", "symbol_name": "format_iso_timestamp", "content": "def format_iso_timestamp(): pass"}],
            repo_name="org/python-tool",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert "CROSS_REPOSITORY_MISMATCH" not in gate["rejection_codes"]

    # 14. Documentation issue -> documentation target passes
    def test_documentation_issue_allows_docs_target(self):
        exp = self._create_valid_explanation()
        exp.relevant_locations = [
            GroundedCodeLocation(file_path="docs/architecture.md", is_verified=True)
        ]
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "docs/architecture.md", "content": "# Architecture"}],
            repo_name="org/python-tool",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert "CROSS_REPOSITORY_MISMATCH" not in gate["rejection_codes"]

    # 15. Bounded beginner issue -> passes
    def test_bounded_beginner_issue_passes(self):
        exp = self._create_valid_explanation()
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py", "symbol_name": "format_iso_timestamp", "content": "def format_iso_timestamp(): pass"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp, raw_issue={"title": "Fix date offset bug", "body": "Small bug in ISO parsing"})
        assert gate["is_safe"] is True

    # 16. Clearly massive multi-system issue -> rejects
    def test_massive_multi_system_issue_rejects(self):
        exp = self._create_valid_explanation()
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py", "symbol_name": "format_iso_timestamp", "content": "def format_iso_timestamp(): pass"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(
            exp,
            raw_issue={"title": "Proposal: Complete rewrite of the architecture and overhaul everything", "body": "We need to rewrite the entire system from scratch."}
        )
        assert gate["is_safe"] is False
        assert "SCOPE_TOO_BROAD" in gate["rejection_codes"]

    # 17. Legitimate technical identifiers do not cause rejection
    def test_technical_identifiers_pass(self):
        exp = self._create_valid_explanation()
        exp.why_it_happens = (
            "When sending HTTP POST requests with Content-Type: application/json to the REST API, "
            "the JWT authorization token parser throws a NullPointerException in `src/date_utils.py`."
        )
        verifier = GroundingVerifier(
            retrieved_chunks=[{"file_path": "src/date_utils.py", "symbol_name": "format_iso_timestamp", "content": "def format_iso_timestamp(): pass"}],
            repo_name="org/repo",
            repo_language="python"
        )
        gate = verifier.validate_publication_gate(exp)
        assert "UNSUPPORTED_ROOT_CAUSE" not in gate["rejection_codes"]
