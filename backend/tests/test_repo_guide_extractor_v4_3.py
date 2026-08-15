"""
GitNova v4.3 — Phase E Repository Contribution Guide Unit Tests
================================================================
Tests all 15 Phase E requirement scenarios for repository guide extraction and journey integration.
"""

import pytest
from app.schemas.explanation import RepositoryContributionGuide
from app.pipeline.repo_guide_extractor import RepoGuideExtractor
from app.pipeline.journey_generator import ContributionJourneyGenerator


# Test 1: CONTRIBUTING.md extraction
def test_contributing_md_extraction():
    raw_md = """
    # Contributing to CustomRepo
    Please run `pytest` before submitting a PR.
    Use `pre-commit run --all-files` for linting.
    Sign the CLA before submitting.
    """
    guide = RepoGuideExtractor.extract_guide("org/customrepo", raw_contributing_md=raw_md)
    assert guide.guide_found is True
    assert guide.guide_source == "CONTRIBUTING.md"
    assert guide.test_command == "pytest"
    assert guide.test_command_source == "CONTRIBUTING.md"
    assert guide.lint_command == "pre-commit run --all-files"
    assert guide.cla_required is True


# Test 2: Missing CONTRIBUTING.md handling
def test_missing_contributing_md_handling():
    guide = RepoGuideExtractor.extract_guide("unknown/empty_repo")
    assert guide.guide_found is False
    assert guide.guide_source == "NOT_FOUND"
    assert guide.test_command == "Not verified — check repository documentation."
    assert guide.test_command_source == "NOT_VERIFIED"


# Test 3: CI test-command extraction (.github/workflows/*.yml)
def test_ci_test_command_extraction():
    ci_config = {"source": ".github/workflows/tests.yml", "runner": "pytest tests/"}
    guide = RepoGuideExtractor.extract_guide("org/ci_repo", ci_config=ci_config)
    assert guide.guide_found is True
    assert guide.test_command == "pytest"
    assert guide.test_command_source == ".github/workflows/tests.yml"


# Test 4: Missing test command handling (Zero Fabrication Rule)
def test_missing_test_command_zero_fabrication():
    guide = RepoGuideExtractor.extract_guide("unknown/no_ci_repo")
    assert guide.test_command == "Not verified — check repository documentation."
    assert guide.test_command_source == "NOT_VERIFIED"
    assert "Not verified" in guide.test_command


# Test 5: Lint command extraction
def test_lint_command_extraction():
    raw_md = "Use `ruff check .` for linting."
    guide = RepoGuideExtractor.extract_guide("org/lint_repo", raw_contributing_md=raw_md)
    assert guide.lint_command == "ruff check ."
    assert guide.lint_command_source == "CONTRIBUTING.md"


# Test 6: Format command extraction
def test_format_command_extraction():
    guide = RepoGuideExtractor.extract_guide("org/format_repo")
    assert guide.format_command_source == "NOT_VERIFIED"


# Test 7: PR guidance extraction
def test_pr_guidance_extraction():
    raw_md = "Please create a newsfragment entry before opening your pull request."
    guide = RepoGuideExtractor.extract_guide("org/pr_repo", raw_contributing_md=raw_md)
    assert "newsfragment" in guide.pull_request_guidance.lower()


# Test 8: Source attribution retention
def test_source_attribution_retention():
    raw_md = "Run `cargo test` to execute tests."
    guide = RepoGuideExtractor.extract_guide("tokio-rs/tokio_test", raw_contributing_md=raw_md)
    assert guide.test_command == "cargo test"
    assert guide.test_command_source == "CONTRIBUTING.md"


# Test 9: Freshness timestamp existence
def test_freshness_timestamp_existence():
    guide = RepoGuideExtractor.extract_guide("org/fresh_repo")
    assert guide.last_verified_at is not None
    assert "T" in guide.last_verified_at


# Test 10: Repository-level caching
def test_repo_level_caching():
    guide1 = RepoGuideExtractor.extract_guide("pallets/flask")
    cached = RepoGuideExtractor.get_cached_guide("pallets/flask")
    assert cached is not None
    assert cached.repo_full_name == "pallets/flask"


# Test 11: No fabricated commands rule
def test_no_fabricated_commands_rule():
    issue_stub = {
        "repo_full_name": "unknown/unverified_project",
        "github_issue_number": 1,
        "title": "Bug in unverified project",
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    test_stage = journey.stages[7]
    assert test_stage.commands == []
    assert "could not verify" in test_stage.explanation.lower()
    assert any("Source: NOT_VERIFIED" in e for e in test_stage.evidence)


# Test 12: Journey consumes repository guide
def test_journey_consumes_repository_guide():
    repo_guide = {
        "raw_contributing_md": "Run `pytest` to execute tests. Use `pre-commit` for linting."
    }
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context bug",
        "explanation": {},
        "repository_contribution_guide": repo_guide
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    test_stage = journey.stages[7]
    assert "pytest" in test_stage.commands
    assert any("Source: CONTRIBUTING.md" in e for e in test_stage.evidence)


# Test 13: Stage 8 receives verified test command or Not Verified notice
def test_stage_8_receives_verified_test_command():
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context bug",
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    test_stage = journey.stages[7]
    assert "pytest" in test_stage.commands


# Test 14: Stage 9 receives verified PR guidance
def test_stage_9_receives_verified_pr_guidance():
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context bug",
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    pr_stage = journey.stages[8]
    assert any("Fixes #6123" in step for step in pr_stage.steps)


# Test 15: Stage 10 receives repository-specific review requirements
def test_stage_10_receives_review_requirements():
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context bug",
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    review_stage = journey.stages[9]
    assert "https://github.com/pallets/flask/issues/6123" in review_stage.evidence[0]
