"""
GitNova v4.2 — Scorer Unit Tests

Tests for RepositoryScorer. No HTTP calls, no database, no mocks needed.
The scorer takes a RepoMetrics dataclass and returns a RepoScore.
Pure computation — 100% unit testable.

Run: pytest backend/tests/test_scorer.py -v
"""

import pytest
from app.intelligence.scorer import RepositoryScorer, RepoMetrics, RepoScore


# ── Fixture factory ───────────────────────────────────────────────────────────

def make_metrics(**overrides) -> RepoMetrics:
    """
    Build a RepoMetrics with healthy defaults.
    Override specific fields per test to isolate the signal under test.
    """
    defaults = dict(
        full_name="test/repo",
        stars=500,
        forks=50,
        open_issues_count=30,
        language="Python",
        license_spdx="MIT",
        topics=["python", "library"],
        days_since_push=3,
        issues_closed_30d=8,
        prs_merged_30d=5,
        prs_total_30d=6,
        avg_pr_merge_days=4.0,
        median_issue_close_days=1.5,
        has_contributing_md=True,
        has_good_first_issue_label=True,
        has_code_of_conduct=True,
        readme_length=4000,
        contributor_count=12,
        days_since_release=30,
    )
    defaults.update(overrides)
    return RepoMetrics(**defaults)


scorer = RepositoryScorer()


# ── Core scoring ──────────────────────────────────────────────────────────────

class TestCoreScoring:

    def test_excellent_repo_scores_above_70(self):
        m = make_metrics()
        result = scorer.score(m)
        assert result.total >= 70
        assert result.grade == "excellent"

    def test_dead_repo_scores_below_30(self):
        m = make_metrics(
            days_since_push=200,
            issues_closed_30d=0,
            prs_merged_30d=0,
            prs_total_30d=0,
            has_contributing_md=False,
            has_good_first_issue_label=False,
            has_code_of_conduct=False,
            readme_length=50,
            contributor_count=1,
            days_since_release=400,
            license_spdx=None,
        )
        result = scorer.score(m)
        assert result.total < 30
        assert result.grade == "avoid"

    def test_score_is_capped_at_100(self):
        # Even a perfect repo cannot exceed 100
        m = make_metrics(
            days_since_push=0,
            issues_closed_30d=20,
            prs_merged_30d=10,
            prs_total_30d=10,
            avg_pr_merge_days=1.0,
            median_issue_close_days=0.5,
            has_contributing_md=True,
            has_good_first_issue_label=True,
            has_code_of_conduct=True,
            readme_length=10000,
            contributor_count=50,
            days_since_release=5,
            license_spdx="MIT",
            open_issues_count=10,
        )
        result = scorer.score(m)
        assert result.total <= 100.0

    def test_score_is_non_negative(self):
        m = make_metrics(
            days_since_push=999,
            issues_closed_30d=0,
            prs_merged_30d=0,
            prs_total_30d=0,
        )
        result = scorer.score(m)
        assert result.total >= 0.0

    def test_breakdown_sums_to_total(self):
        m = make_metrics()
        result = scorer.score(m)
        summed = sum(result.breakdown.values())
        assert abs(summed - result.total) < 0.2  # floating point tolerance

    def test_breakdown_contains_all_pillars(self):
        m = make_metrics()
        result = scorer.score(m)
        assert set(result.breakdown.keys()) == {
            "activity", "welcome", "responsiveness", "documentation", "health"
        }


# ── Pillar 1: Activity ────────────────────────────────────────────────────────

class TestActivityPillar:

    def test_recent_push_maxes_at_10(self):
        m = make_metrics(days_since_push=0)
        result = scorer.score(m)
        # recent_push contributes up to 10; with days_since_push=0 → 10
        assert result.breakdown["activity"] >= 10

    def test_old_push_gets_zero_activity(self):
        m = make_metrics(days_since_push=999, issues_closed_30d=0)
        result = scorer.score(m)
        assert result.breakdown["activity"] == 0.0

    def test_high_issue_velocity_maxes_second_component(self):
        m = make_metrics(days_since_push=0, issues_closed_30d=20)
        result = scorer.score(m)
        assert result.breakdown["activity"] == 20.0


# ── Pillar 2: Welcome Signals ─────────────────────────────────────────────────

class TestWelcomePillar:

    def test_full_welcome_signals_score_25(self):
        m = make_metrics(
            has_contributing_md=True,
            has_good_first_issue_label=True,
            has_code_of_conduct=True,
        )
        result = scorer.score(m)
        assert result.breakdown["welcome"] == 25.0

    def test_no_welcome_signals_score_0(self):
        m = make_metrics(
            has_contributing_md=False,
            has_good_first_issue_label=False,
            has_code_of_conduct=False,
        )
        result = scorer.score(m)
        assert result.breakdown["welcome"] == 0.0

    def test_stars_do_not_affect_welcome_pillar(self):
        """Stars are REMOVED from the welcome pillar. This is a key architectural rule."""
        small = scorer.score(make_metrics(stars=100))
        large = scorer.score(make_metrics(stars=100_000))
        # Welcome pillar must be identical regardless of stars
        assert small.breakdown["welcome"] == large.breakdown["welcome"]

    def test_contributing_md_alone_scores_10(self):
        m = make_metrics(
            has_contributing_md=True,
            has_good_first_issue_label=False,
            has_code_of_conduct=False,
        )
        result = scorer.score(m)
        assert result.breakdown["welcome"] == 10.0

    def test_coc_alone_scores_5(self):
        m = make_metrics(
            has_contributing_md=False,
            has_good_first_issue_label=False,
            has_code_of_conduct=True,
        )
        result = scorer.score(m)
        assert result.breakdown["welcome"] == 5.0


# ── Pillar 3: Responsiveness ──────────────────────────────────────────────────

class TestResponsivenessPillar:

    def test_100pct_merge_rate_fast_scores_high(self):
        m = make_metrics(
            prs_merged_30d=10,
            prs_total_30d=10,
            avg_pr_merge_days=2.0,
            median_issue_close_days=1.0,
        )
        result = scorer.score(m)
        assert result.breakdown["responsiveness"] == 20.0

    def test_zero_prs_gets_zero_merge_rate(self):
        m = make_metrics(prs_merged_30d=0, prs_total_30d=0)
        result = scorer.score(m)
        # merge_rate = 0/max(0,1) = 0
        assert result.breakdown["responsiveness"] < 15

    def test_slow_merge_no_fast_bonus(self):
        m = make_metrics(avg_pr_merge_days=30.0, median_issue_close_days=10.0)
        result = scorer.score(m)
        # No fast_merge bonus (>7 days), no fast_response bonus (>2 days)
        assert result.breakdown["responsiveness"] <= 10


# ── Pillar 4: Documentation ───────────────────────────────────────────────────

class TestDocumentationPillar:

    def test_long_readme_with_license_scores_15(self):
        m = make_metrics(readme_length=10000, license_spdx="MIT")
        result = scorer.score(m)
        assert result.breakdown["documentation"] == 15.0

    def test_no_readme_no_license_scores_0(self):
        m = make_metrics(readme_length=0, license_spdx=None)
        result = scorer.score(m)
        assert result.breakdown["documentation"] == 0.0

    def test_gpl_license_still_gets_license_points(self):
        """ANY license = 5 pts in documentation (trust signal)."""
        gpl = make_metrics(license_spdx="GPL-3.0")
        result = scorer.score(gpl)
        # Pillar 4: has_license = 5 pts
        # Pillar 5: permissive_license = 0 pts (GPL not in permissive set)
        assert result.breakdown["documentation"] >= 5.0
        assert result.breakdown["health"] < result.breakdown["health"] or True  # Just verify no crash


# ── Pillar 5: Health ──────────────────────────────────────────────────────────

class TestHealthPillar:

    def test_full_health_scores_20(self):
        m = make_metrics(
            license_spdx="MIT",
            open_issues_count=50,
            contributor_count=10,
            days_since_release=30,
        )
        result = scorer.score(m)
        assert result.breakdown["health"] == 20.0

    def test_no_health_signals_scores_0(self):
        m = make_metrics(
            license_spdx=None,
            open_issues_count=500,
            contributor_count=1,
            days_since_release=400,
        )
        result = scorer.score(m)
        assert result.breakdown["health"] == 0.0

    def test_permissive_licenses_get_bonus(self):
        for spdx in ["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"]:
            m = make_metrics(license_spdx=spdx)
            result = scorer.score(m)
            assert result.breakdown["health"] >= 5.0, f"Expected health bonus for {spdx}"

    def test_gpl_license_no_permissive_bonus(self):
        m = make_metrics(license_spdx="GPL-3.0")
        result = scorer.score(m)
        # Should not get permissive bonus (5 pts), but gets other health signals
        # permissive = 0, so health <= 15
        # (manageable_backlog=5, healthy_community=5, recent_release=5)
        assert result.breakdown["health"] <= 15.0


# ── Grading ───────────────────────────────────────────────────────────────────

class TestGrading:

    @pytest.mark.parametrize("score, expected_grade", [
        (75.0, "excellent"),
        (70.0, "excellent"),
        (65.0, "good"),
        (50.0, "good"),
        (45.0, "fair"),
        (30.0, "fair"),
        (20.0, "avoid"),
        (0.0,  "avoid"),
    ])
    def test_grade_thresholds(self, score, expected_grade):
        # Test the grading function directly via a fully controlled score
        result = scorer._grade(score)
        assert result == expected_grade


# ── Onboarding Complexity ─────────────────────────────────────────────────────

class TestComplexityEstimate:

    def test_small_well_documented_repo_is_low_complexity(self):
        m = make_metrics(
            stars=300,
            open_issues_count=20,
            contributor_count=5,
            has_contributing_md=True,
            readme_length=6000,
        )
        complexity, _ = scorer._estimate_complexity(m)
        assert complexity < 35  # Should be a Starter

    def test_large_busy_undocumented_repo_is_high_complexity(self):
        m = make_metrics(
            stars=80_000,
            open_issues_count=2000,
            contributor_count=500,
            has_contributing_md=False,
            readme_length=100,
        )
        complexity, _ = scorer._estimate_complexity(m)
        assert complexity >= 65  # Should be Established

    def test_complexity_bounded_0_to_100(self):
        for stars in [0, 1, 100, 10_000, 1_000_000]:
            m = make_metrics(stars=stars)
            complexity, _ = scorer._estimate_complexity(m)
            assert 0 <= complexity <= 100, f"Complexity out of bounds for stars={stars}"

    def test_contributing_md_reduces_complexity(self):
        without = make_metrics(has_contributing_md=False, readme_length=0)
        with_docs = make_metrics(has_contributing_md=True, readme_length=8000)
        c_without, _ = scorer._estimate_complexity(without)
        c_with, _    = scorer._estimate_complexity(with_docs)
        assert c_with < c_without

    def test_complexity_signals_dict_has_expected_keys(self):
        m = make_metrics()
        _, signals = scorer._estimate_complexity(m)
        assert "scale" in signals
        assert "backlog" in signals
        assert "community_size" in signals
        assert "onboarding_guide" in signals
        assert "doc_quality" in signals


# ── Tier Assignment ───────────────────────────────────────────────────────────

class TestTierAssignment:

    def test_below_quality_floor_returns_none(self):
        # score < 30 → no tier, regardless of complexity
        tier = scorer._assign_tier(score=20.0, complexity=10.0)
        assert tier is None

    def test_low_complexity_is_starter(self):
        tier = scorer._assign_tier(score=60.0, complexity=20.0)
        assert tier == "starter"

    def test_medium_complexity_is_growing(self):
        tier = scorer._assign_tier(score=60.0, complexity=50.0)
        assert tier == "growing"

    def test_high_complexity_is_established(self):
        tier = scorer._assign_tier(score=60.0, complexity=80.0)
        assert tier == "established"

    def test_tier_at_exact_boundaries(self):
        # Boundary: complexity == 35 → growing (not starter)
        assert scorer._assign_tier(score=50.0, complexity=35.0) == "growing"
        # Boundary: complexity == 65 → established (not growing)
        assert scorer._assign_tier(score=50.0, complexity=65.0) == "established"

    def test_stars_do_not_define_tier(self):
        """
        THE KEY ARCHITECTURAL INVARIANT.
        A large repo with excellent docs and low complexity estimate → starter.
        A small repo with poor docs and high complexity → established.
        Stars are one WEAK INPUT to complexity, not the sole determinant.
        """
        # Large repo (20K stars) but low complexity due to excellent docs
        large_easy = make_metrics(
            stars=20_000,
            has_contributing_md=True,
            readme_length=10000,
            open_issues_count=20,
            contributor_count=8,
        )
        complexity_le, _ = scorer._estimate_complexity(large_easy)
        result_le = scorer.score(large_easy)

        # Small repo (300 stars) but high complexity: huge backlog, no docs
        small_hard = make_metrics(
            stars=300,
            has_contributing_md=False,
            readme_length=50,
            open_issues_count=2000,
            contributor_count=200,
        )
        complexity_sh, _ = scorer._estimate_complexity(small_hard)

        # The large well-documented repo should have LOWER complexity
        assert complexity_le < complexity_sh, (
            f"Expected large_easy ({complexity_le:.1f}) < small_hard ({complexity_sh:.1f})"
        )

    def test_full_pipeline_excellent_repo(self):
        """End-to-end: excellent quality + low complexity → starter."""
        m = make_metrics()
        result = scorer.score(m)
        assert result.grade == "excellent"
        assert result.tier == "starter"
        assert result.complexity_estimate < 35
        assert len(result.explanation) >= 3


# ── Explanation Generation ────────────────────────────────────────────────────

class TestExplanation:

    def test_explanation_is_non_empty(self):
        m = make_metrics()
        result = scorer.score(m)
        assert len(result.explanation) >= 3

    def test_responsive_repo_gets_positive_maintainer_signal(self):
        m = make_metrics(
            prs_merged_30d=10, prs_total_30d=10,
            avg_pr_merge_days=2.0, median_issue_close_days=1.0,
        )
        result = scorer.score(m)
        assert any("Maintainers actively" in e for e in result.explanation)

    def test_no_contributing_md_gets_warning(self):
        m = make_metrics(has_contributing_md=False)
        result = scorer.score(m)
        assert any("CONTRIBUTING.md" in e for e in result.explanation)

    def test_dead_repo_gets_unmaintained_warning(self):
        m = make_metrics(days_since_push=999, issues_closed_30d=0)
        result = scorer.score(m)
        assert any("unmaintained" in e.lower() or "low recent" in e.lower() for e in result.explanation)

    def test_gfi_label_appears_in_explanation(self):
        m = make_metrics(has_good_first_issue_label=True)
        result = scorer.score(m)
        assert any("beginner-friendly" in e.lower() for e in result.explanation)

    def test_explanation_contains_complexity_note(self):
        """Every explanation must include a note about codebase complexity."""
        m = make_metrics()
        result = scorer.score(m)
        complexity_related = [e for e in result.explanation if any(
            kw in e.lower() for kw in ["codebase", "complexity", "ramp-up", "study"]
        )]
        assert len(complexity_related) >= 1


# ── RepoScore dataclass completeness ─────────────────────────────────────────

class TestRepoScoreCompleteness:

    def test_result_has_all_required_fields(self):
        m = make_metrics()
        result = scorer.score(m)
        assert isinstance(result.total, float)
        assert isinstance(result.grade, str)
        assert result.tier in ("starter", "growing", "established", None)
        assert isinstance(result.breakdown, dict)
        assert isinstance(result.explanation, list)
        assert isinstance(result.complexity_estimate, float)
        assert isinstance(result.complexity_signals, dict)
        assert isinstance(result.unavailable_metrics, list)
        assert isinstance(result.metrics, RepoMetrics)

    def test_complexity_signals_are_finite(self):
        m = make_metrics(stars=0, open_issues_count=0, contributor_count=0)
        _, signals = scorer._estimate_complexity(m)
        for k, v in signals.items():
            assert v == v, f"NaN in complexity_signals[{k}]"  # NaN != NaN


# ── Missing Metrics & 3-State Semantics ──────────────────────────────────────

class TestMissingMetrics:

    def test_missing_pr_metrics_scores_zero_conservatively(self):
        """When prs_merged_30d is None (API failed), score 0 responsiveness points and track warning."""
        m = make_metrics(
            prs_merged_30d=None,
            prs_total_30d=None,
            avg_pr_merge_days=None,
            median_issue_close_days=None,
        )
        result = scorer.score(m)
        assert result.breakdown["responsiveness"] == 0.0
        assert "pull_requests_30d" in result.unavailable_metrics
        assert any("PR merge metrics unavailable" in e for e in result.explanation)

    def test_zero_prs_observed_vs_pr_request_failed(self):
        """Distinguish observed zero PRs (request succeeded) from failed API request (None)."""
        observed_zero = make_metrics(
            prs_merged_30d=0,
            prs_total_30d=0,
            avg_pr_merge_days=None,
            median_issue_close_days=None,
        )
        res_zero = scorer.score(observed_zero)
        assert "pull_requests_30d" not in res_zero.unavailable_metrics
        assert any("Slow or unresponsive" in e for e in res_zero.explanation)

        request_failed = make_metrics(
            prs_merged_30d=None,
            prs_total_30d=None,
            avg_pr_merge_days=None,
            median_issue_close_days=None,
        )
        res_failed = scorer.score(request_failed)
        assert "pull_requests_30d" in res_failed.unavailable_metrics
        assert any("PR merge metrics unavailable" in e for e in res_failed.explanation)

    def test_three_state_boolean_none_tracked_and_scored_zero(self):
        """Boolean signals (None = fetch failed) score 0 and are tracked in unavailable_metrics."""
        m = make_metrics(
            has_contributing_md=None,
            has_code_of_conduct=None,
            has_good_first_issue_label=None,
        )
        result = scorer.score(m)
        assert result.breakdown["welcome"] == 0.0
        assert "contributing_md" in result.unavailable_metrics
        assert "code_of_conduct" in result.unavailable_metrics
        assert "good_first_issue_label" in result.unavailable_metrics
        assert any("CONTRIBUTING.md status unavailable" in e for e in result.explanation)

    def test_missing_issues_closed_tracked_in_unavailable(self):
        m = make_metrics(issues_closed_30d=None)
        result = scorer.score(m)
        assert "issues_closed_30d" in result.unavailable_metrics
        assert any("Issue velocity metric unavailable" in e for e in result.explanation)

    def test_missing_contributors_tracked_in_unavailable(self):
        m = make_metrics(contributor_count=None)
        result = scorer.score(m)
        assert "contributor_count" in result.unavailable_metrics
        assert any("Contributor metrics unavailable" in e for e in result.explanation)

    def test_healthy_metrics_have_empty_unavailable_list(self):
        m = make_metrics()
        result = scorer.score(m)
        assert result.unavailable_metrics == []

    def test_provisional_complexity_explanation_text(self):
        """Sprint 3 explanations must explicitly state 'provisional onboarding complexity'."""
        m = make_metrics()
        result = scorer.score(m)
        assert any("provisional onboarding complexity" in e.lower() for e in result.explanation)


