"""
GitNova v4.2 — API Model Unit Tests

Tests for Pydantic response models in main.py.
Verifies field contracts, computed properties, and renamed pillars.
No HTTP server required — pure model instantiation.

Run: pytest tests/test_api_models.py -v
"""

from uuid import UUID
from datetime import datetime
import pytest

from app.main import RepoOut, IssueOut, ScoreBreakdown


# ── Fixtures ─────────────────────────────────────────────────────────────────

REPO_UUID = UUID("00000000-0000-0000-0000-000000000001")
ISSUE_UUID = UUID("00000000-0000-0000-0000-000000000002")

VALID_BREAKDOWN = {
    "activity": 19.0,
    "welcome": 10.0,
    "responsiveness": 0.0,
    "documentation": 8.3,
    "health": 15.0,
}


def make_repo(**overrides) -> RepoOut:
    defaults = dict(
        id=REPO_UUID,
        full_name="pallets/flask",
        tier="growing",
        score=52.3,
        score_grade="good",
        score_breakdown=VALID_BREAKDOWN,
        score_explanation=["✓ Active repo", "⚠ Moderate provisional onboarding complexity"],
        complexity_estimate=38.7,
        unavailable_metrics=[],
        topics=["flask", "python", "web-framework"],
        stars=72096,
        language="Python",
        description="A simple framework for building web applications.",
        last_scored_at=datetime(2026, 8, 1, 12, 0, 0),
    )
    defaults.update(overrides)
    return RepoOut(**defaults)


def make_issue(**overrides) -> IssueOut:
    defaults = dict(
        id=ISSUE_UUID,
        repo_id=REPO_UUID,
        repo_full_name="pallets/flask",
        github_issue_number=5621,
        repo_tier="growing",
        repo_score=52.3,
        title="Fix incorrect error message in debug mode",
        ai_hint="1. Open src/app.py line 42\n2. Change message to...",
        quality_score=80,
        quality_grade="high",
        difficulty=None,
        estimated_time=None,
        competition_level="low",
        freshness_label="Updated 2 days ago",
        created_at=datetime(2026, 7, 30, 9, 0, 0),
    )
    defaults.update(overrides)
    return IssueOut(**defaults)


# ── ScoreBreakdown ────────────────────────────────────────────────────────────

class TestScoreBreakdown:

    def test_welcome_field_exists(self):
        """Pillar was renamed from 'beginner' to 'welcome' in Sprint 3."""
        bd = ScoreBreakdown(**VALID_BREAKDOWN)
        assert bd.welcome == 10.0

    def test_beginner_field_does_not_exist(self):
        """Old 'beginner' field must not exist — catches stale field regression."""
        bd = ScoreBreakdown(**VALID_BREAKDOWN)
        assert not hasattr(bd, "beginner")

    def test_all_five_pillars_present(self):
        bd = ScoreBreakdown(**VALID_BREAKDOWN)
        assert hasattr(bd, "activity")
        assert hasattr(bd, "welcome")
        assert hasattr(bd, "responsiveness")
        assert hasattr(bd, "documentation")
        assert hasattr(bd, "health")

    def test_breakdown_rejects_unknown_pillar(self):
        """Extra fields should not be accepted silently."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ScoreBreakdown(
                activity=10, welcome=10, responsiveness=5,
                documentation=5, health=5,
                unknown_pillar=99,  # should error
            )


# ── RepoOut ───────────────────────────────────────────────────────────────────

class TestRepoOut:

    def test_basic_instantiation(self):
        repo = make_repo()
        assert repo.full_name == "pallets/flask"
        assert repo.score == 52.3

    def test_id_is_uuid(self):
        repo = make_repo()
        assert isinstance(repo.id, UUID)

    def test_complexity_estimate_is_optional(self):
        """complexity_estimate may be None (not yet scored by Sprint 5)."""
        repo = make_repo(complexity_estimate=None)
        assert repo.complexity_estimate is None

    def test_complexity_estimate_present(self):
        repo = make_repo()
        assert repo.complexity_estimate == 38.7

    def test_unavailable_metrics_defaults_empty(self):
        repo = make_repo()
        assert repo.unavailable_metrics == []

    def test_unavailable_metrics_can_have_values(self):
        repo = make_repo(unavailable_metrics=["pull_requests_30d", "contributor_count"])
        assert "pull_requests_30d" in repo.unavailable_metrics

    def test_topics_is_list(self):
        repo = make_repo()
        assert isinstance(repo.topics, list)
        assert "python" in repo.topics

    def test_topics_can_be_empty(self):
        repo = make_repo(topics=[])
        assert repo.topics == []

    def test_tier_can_be_none(self):
        """Repos below quality floor have tier=None."""
        repo = make_repo(tier=None)
        assert repo.tier is None

    def test_score_breakdown_uses_welcome_not_beginner(self):
        repo = make_repo()
        assert repo.score_breakdown.welcome == 10.0
        assert not hasattr(repo.score_breakdown, "beginner")


# ── IssueOut ─────────────────────────────────────────────────────────────────

class TestIssueOut:

    def test_basic_instantiation(self):
        issue = make_issue()
        assert issue.title == "Fix incorrect error message in debug mode"

    def test_id_is_uuid(self):
        issue = make_issue()
        assert isinstance(issue.id, UUID)

    def test_repo_id_is_uuid(self):
        issue = make_issue()
        assert isinstance(issue.repo_id, UUID)

    def test_github_url_computed_dynamically(self):
        """github_url is not stored — it's computed from repo_full_name + github_issue_number."""
        issue = make_issue(repo_full_name="encode/httpx", github_issue_number=999)
        assert issue.github_url == "https://github.com/encode/httpx/issues/999"

    def test_github_url_format(self):
        issue = make_issue()
        assert issue.github_url == "https://github.com/pallets/flask/issues/5621"
        assert issue.github_url.startswith("https://github.com/")

    def test_github_url_not_in_db_fields(self):
        """github_url is a computed_field — should not need to be passed as input."""
        issue = IssueOut(
            id=ISSUE_UUID,
            repo_id=REPO_UUID,
            repo_full_name="tiangolo/fastapi",
            github_issue_number=1000,
            repo_tier="starter",
            repo_score=65.0,
            title="Test issue",
            quality_score=70,
            quality_grade="high",
            created_at=datetime.now(),
            ai_hint=None, difficulty=None, estimated_time=None,
            competition_level=None, freshness_label=None,
        )
        assert issue.github_url == "https://github.com/tiangolo/fastapi/issues/1000"

    def test_difficulty_is_str_not_enum(self):
        """V1 difficulty is free-form string, not constrained enum."""
        issue_easy = make_issue(difficulty="easy")
        issue_custom = make_issue(difficulty="beginner-friendly")
        assert issue_easy.difficulty == "easy"
        assert issue_custom.difficulty == "beginner-friendly"

    def test_difficulty_can_be_none(self):
        issue = make_issue(difficulty=None)
        assert issue.difficulty is None

    def test_repo_tier_can_be_none(self):
        issue = make_issue(repo_tier=None)
        assert issue.repo_tier is None
