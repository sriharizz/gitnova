"""
GitNova v4.2 — Repository Qualification Engine: Scorer

Two distinct concepts are computed here:

1. CONTRIBUTION SUCCESS SCORE (0-100)
   Measures the quality of the contribution ENVIRONMENT.
   Answers: "If I submit a PR, will anyone review it? Do they welcome beginners?"
   Five pillars: Activity, Welcome Signals, Responsiveness, Documentation, Health.

2. ONBOARDING COMPLEXITY ESTIMATE (0-100)
   Measures how difficult it is to ENTER and understand the codebase.
   Answers: "Can I understand this repository without months of study?"
   PROVISIONAL in Sprint 3 — will be enhanced in Sprint 5 with file_count,
   total_loc, and directory_depth from cloned repository structure.

3. TIER
   Derived from complexity (NOT stars). Gated by minimum quality.
   starter (<35 complexity) | growing (35-64) | established (65+)

MISSING METRIC SEMANTICS:
   Distinguishes observed 0/False from None (unavailable/failed API call).
   Boolean signals (CONTRIBUTING.md, CODE_OF_CONDUCT.md, good-first-issue label) use 3-state
   semantics: True (present), False (confirmed absent via 404), None (API fetch failed).
   If a metric is None (unavailable):
     - Receives 0 points (conservative policy — no unearned credit)
     - Added to unavailable_metrics tracking array
     - Exposes an explicit warning in explanation: "⚠ [metric] unavailable — score conservative"
     - Emits a warning log for observability
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Input data ────────────────────────────────────────────────────────────────

@dataclass
class RepoMetrics:
    """
    All raw signals collected from GitHub API for one repository.
    Populated by collector.py — scorer.py never calls GitHub directly.

    Fields with Optional[T] = None represent missing/unavailable data due to API errors,
    as distinct from observed zero or False values.
    """
    # Basic metadata
    full_name: str
    stars: int
    forks: int
    open_issues_count: int
    language: Optional[str]
    license_spdx: Optional[str]
    topics: List[str] = field(default_factory=list)

    # Activity signals (None = API fetch failed)
    days_since_push: int = 999
    issues_closed_30d: Optional[int] = None

    # Responsiveness signals (None = API fetch failed)
    prs_merged_30d: Optional[int] = None
    prs_total_30d: Optional[int] = None
    avg_pr_merge_days: Optional[float] = None
    median_issue_close_days: Optional[float] = None

    # Welcome signals (3-state: True / False / None)
    has_contributing_md: Optional[bool] = None
    has_good_first_issue_label: Optional[bool] = None
    has_code_of_conduct: Optional[bool] = None

    # Documentation signals (None = API fetch failed)
    readme_length: Optional[int] = None

    # Health signals (None = API fetch failed)
    contributor_count: Optional[int] = None
    days_since_release: Optional[int] = None


# ── Output data ───────────────────────────────────────────────────────────────

@dataclass
class RepoScore:
    """
    Full scoring result for one repository.
    This is what gets written to the repos table.
    """
    total: float                          # Contribution Success Score (0-100)
    grade: str                            # excellent | good | fair | avoid
    tier: Optional[str]                   # starter | growing | established | None
    breakdown: Dict[str, float]           # per-pillar scores
    explanation: List[str]                # human-readable, deterministic
    complexity_estimate: float            # 0-100 (PROVISIONAL until Sprint 5)
    complexity_signals: Dict[str, float]  # what fed into complexity (transparency)
    unavailable_metrics: List[str]        # metrics that failed to collect (confidence reduction)
    metrics: RepoMetrics                  # raw inputs for debugging


# ── Scorer ────────────────────────────────────────────────────────────────────

class RepositoryScorer:
    """
    Computes Contribution Success Score and Onboarding Complexity for a repository.

    Usage:
        scorer = RepositoryScorer()
        result = scorer.score(metrics)
    """

    def score(self, metrics: RepoMetrics) -> RepoScore:
        unavailable_metrics: List[str] = []

        # Identify missing metrics (None = API fetch failed)
        if metrics.issues_closed_30d is None:
            unavailable_metrics.append("issues_closed_30d")
        if metrics.prs_total_30d is None or metrics.prs_merged_30d is None:
            unavailable_metrics.append("pull_requests_30d")
        if metrics.has_contributing_md is None:
            unavailable_metrics.append("contributing_md")
        if metrics.has_code_of_conduct is None:
            unavailable_metrics.append("code_of_conduct")
        if metrics.has_good_first_issue_label is None:
            unavailable_metrics.append("good_first_issue_label")
        if metrics.readme_length is None:
            unavailable_metrics.append("readme_length")
        if metrics.contributor_count is None:
            unavailable_metrics.append("contributor_count")

        # ── Quality score (5 pillars) ─────────────────────────────────────────
        activity        = self._score_activity(metrics)
        welcome         = self._score_welcome(metrics)
        responsiveness  = self._score_responsiveness(metrics)
        documentation   = self._score_documentation(metrics)
        health          = self._score_health(metrics)

        total = round(activity + welcome + responsiveness + documentation + health, 1)

        breakdown = {
            "activity":       round(activity, 1),
            "welcome":        round(welcome, 1),
            "responsiveness": round(responsiveness, 1),
            "documentation":  round(documentation, 1),
            "health":         round(health, 1),
        }

        grade = self._grade(total)

        # ── Complexity estimate (provisional) ─────────────────────────────────
        complexity, complexity_signals = self._estimate_complexity(metrics)

        # ── Tier (complexity-based, quality-gated) ────────────────────────────
        tier = self._assign_tier(total, complexity)

        # ── Explanation (deterministic, no LLM) ──────────────────────────────
        explanation = self._generate_explanation(breakdown, metrics, complexity, unavailable_metrics)

        if unavailable_metrics:
            logger.warning("metrics_unavailable", extra={
                "repo": metrics.full_name,
                "unavailable": unavailable_metrics,
                "score_impact": "conservative_zero_applied",
            })

        result = RepoScore(
            total=total,
            grade=grade,
            tier=tier,
            breakdown=breakdown,
            explanation=explanation,
            complexity_estimate=round(complexity, 1),
            complexity_signals=complexity_signals,
            unavailable_metrics=unavailable_metrics,
            metrics=metrics,
        )

        logger.info("repo_scored", extra={
            "repo": metrics.full_name,
            "score": total,
            "grade": grade,
            "tier": tier,
            "complexity": round(complexity, 1),
            "unavailable_count": len(unavailable_metrics),
        })

        return result

    # ── Pillar 1: Activity (20 pts) ───────────────────────────────────────────

    def _score_activity(self, m: RepoMetrics) -> float:
        recent_push    = max(0, 1 - m.days_since_push / 30) * 10
        closed_count   = m.issues_closed_30d if m.issues_closed_30d is not None else 0
        issue_velocity = min(closed_count / 10, 1) * 10
        return recent_push + issue_velocity

    # ── Pillar 2: Welcome Signals (25 pts) ────────────────────────────────────

    def _score_welcome(self, m: RepoMetrics) -> float:
        return (
            (10 if m.has_contributing_md is True else 0) +
            (10 if m.has_good_first_issue_label is True else 0) +
            (5  if m.has_code_of_conduct is True else 0)
        )

    # ── Pillar 3: Responsiveness (20 pts) ────────────────────────────────────

    def _score_responsiveness(self, m: RepoMetrics) -> float:
        # If PR metrics are None (API fetch failed), merge_rate is 0
        if m.prs_merged_30d is None or m.prs_total_30d is None:
            merge_rate = 0.0
        else:
            merge_rate = (m.prs_merged_30d / max(m.prs_total_30d, 1)) * 10

        fast_merge    = 5 if (m.avg_pr_merge_days or 999) < 7 else 0
        fast_response = 5 if (m.median_issue_close_days or 999) < 2 else 0
        return merge_rate + fast_merge + fast_response

    # ── Pillar 4: Documentation (15 pts) ─────────────────────────────────────

    def _score_documentation(self, m: RepoMetrics) -> float:
        readme_len = m.readme_length if m.readme_length is not None else 0
        readme  = min(readme_len / 5000, 1) * 10
        license_present = 5 if m.license_spdx else 0
        return readme + license_present

    # ── Pillar 5: Health (20 pts) ─────────────────────────────────────────────

    def _score_health(self, m: RepoMetrics) -> float:
        permissive = 5 if m.license_spdx in {"MIT", "Apache-2.0", "BSD-3-Clause", "ISC"} else 0
        # open_issues_count < 100 evaluated as a weak backlog/health heuristic
        manageable = 5 if m.open_issues_count < 100 else 0
        contrib_cnt = m.contributor_count if m.contributor_count is not None else 0
        community  = 5 if contrib_cnt > 5 else 0
        recent     = 5 if (m.days_since_release or 999) < 90 else 0
        return permissive + manageable + community + recent

    # ── Grade ─────────────────────────────────────────────────────────────────

    def _grade(self, total: float) -> str:
        if total >= 70: return "excellent"
        if total >= 50: return "good"
        if total >= 30: return "fair"
        return "avoid"

    # ── Onboarding Complexity Estimate (PROVISIONAL) ──────────────────────────
    #
    # Answers: "How difficult is this codebase estimated to be to enter?"
    # PROVISIONAL: Uses GitHub API metadata signals only (stars, backlog count,
    # contributor count, docs). open_issues_count is evaluated strictly as a
    # weak backlog/scale proxy, NOT direct codebase structural complexity.
    # Sprint 5 will add file_count, total_loc, directory_depth from cloned repository structure.

    def _estimate_complexity(self, m: RepoMetrics) -> tuple[float, Dict[str, float]]:
        scale         = min(math.log10(max(m.stars, 1)) / 5, 1.0) * 30          # 0-30
        # open_issues_count evaluated only as a weak backlog scale proxy
        backlog       = min(m.open_issues_count / 500, 1.0) * 20                 # 0-20
        contrib_cnt   = m.contributor_count if m.contributor_count is not None else 1
        community_sz  = min(math.log10(max(contrib_cnt, 1)) / 3, 1.0) * 20        # 0-20

        # Mitigation signals
        onboarding_guide = -10.0 if m.has_contributing_md is True else 0.0
        readme_len       = m.readme_length if m.readme_length is not None else 0
        doc_quality      = -min(readme_len / 8000, 1.0) * 10                     # -10 to 0

        raw = scale + backlog + community_sz + onboarding_guide + doc_quality
        estimate = max(0.0, min(100.0, raw))

        signals = {
            "complexity_source": "provisional",
            "scale":          round(scale, 2),
            "backlog":        round(backlog, 2),
            "community_size": round(community_sz, 2),
            "onboarding_guide": round(onboarding_guide, 2),
            "doc_quality":    round(doc_quality, 2),
        }

        return estimate, signals

    # ── Tier Assignment ───────────────────────────────────────────────────────

    def _assign_tier(self, score: float, complexity: float) -> Optional[str]:
        if score < 30:       # Below quality floor — not healthy enough to recommend
            return None
        if complexity < 35:
            return "starter"
        elif complexity < 65:
            return "growing"
        else:
            return "established"

    def refine_complexity_with_structural_metrics(
        self,
        provisional_complexity: float,
        provisional_signals: Dict[str, Any],
        file_count: int,
        total_loc: int,
        max_directory_depth: int,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Refines onboarding complexity using ground-truth codebase structural metrics.
        Blends provisional API scale metadata with actual LOC, file count, and directory depth.
        Sets complexity_source = "structural" in signals.
        """
        loc_signal = min(math.log10(max(total_loc, 10)) / 5.0, 1.0) * 35.0
        file_signal = min(file_count / 500.0, 1.0) * 15.0
        depth_signal = min(max_directory_depth / 10.0, 1.0) * 10.0

        structural_raw = loc_signal + file_signal + depth_signal

        # Extract gross provisional scale (before documentation discounts)
        provisional_gross = (
            provisional_signals.get("scale", 0.0)
            + provisional_signals.get("backlog", 0.0)
            + provisional_signals.get("community_size", 0.0)
        )
        onboarding_guide = provisional_signals.get("onboarding_guide", 0.0)
        doc_quality = provisional_signals.get("doc_quality", 0.0)

        # 40% provisional API scale + 60% ground-truth codebase structure, minus documentation discounts once
        blended_gross = (provisional_gross * 0.4) + (structural_raw * 0.6)
        blended_raw = blended_gross + onboarding_guide + doc_quality
        refined_complexity = max(0.0, min(100.0, blended_raw))

        refined_signals = dict(provisional_signals)
        refined_signals.update({
            "complexity_source": "structural",
            "total_loc": total_loc,
            "file_count": file_count,
            "max_directory_depth": max_directory_depth,
            "loc_signal": round(loc_signal, 2),
            "file_signal": round(file_signal, 2),
            "depth_signal": round(depth_signal, 2),
            "structural_raw": round(structural_raw, 2),
        })

        return round(refined_complexity, 1), refined_signals

    # ── Explanation Generation ────────────────────────────────────────────────

    def _generate_explanation(
        self,
        breakdown: Dict[str, float],
        m: RepoMetrics,
        complexity: float,
        unavailable_metrics: List[str],
    ) -> List[str]:
        exp: List[str] = []

        # Responsiveness
        if "pull_requests_30d" in unavailable_metrics:
            exp.append("⚠ PR merge metrics unavailable — responsiveness score conservative")
        elif breakdown["responsiveness"] >= 15:
            exp.append("✓ Maintainers actively review contributions")
        elif breakdown["responsiveness"] >= 8:
            exp.append("⚠ Moderate maintainer responsiveness")
        else:
            exp.append("✗ Slow or unresponsive to contributions")

        # Contribution docs (3-state)
        if m.has_contributing_md is True:
            exp.append("✓ Clear contribution documentation (CONTRIBUTING.md)")
        elif m.has_contributing_md is False:
            exp.append("⚠ No CONTRIBUTING.md — contribution process unclear")
        else:
            exp.append("⚠ CONTRIBUTING.md status unavailable — contribution process unconfirmed")

        # Activity
        if "issues_closed_30d" in unavailable_metrics:
            exp.append("⚠ Issue velocity metric unavailable — activity score conservative")
        elif breakdown["activity"] >= 15:
            exp.append("✓ Repository is actively maintained")
        elif breakdown["activity"] >= 8:
            exp.append("⚠ Moderate recent activity")
        else:
            exp.append("✗ Low recent activity — may be unmaintained")

        # Beginner labels
        if m.has_good_first_issue_label is True:
            exp.append("✓ Has beginner-friendly issue labels")
        elif m.has_good_first_issue_label is None:
            exp.append("⚠ Issue label metrics unavailable")

        # Community health
        if "contributor_count" in unavailable_metrics:
            exp.append("⚠ Contributor metrics unavailable — community health score conservative")
        elif breakdown["health"] >= 15:
            exp.append("✓ Healthy community and project governance")
        elif breakdown["health"] <= 5:
            exp.append("⚠ Limited community signals")

        # Provisional Onboarding Complexity (Explicitly provisional for Sprint 3)
        if complexity < 25:
            exp.append("✓ Low provisional onboarding complexity — estimated accessible entry")
        elif complexity < 50:
            exp.append("⚠ Moderate provisional onboarding complexity — expect some ramp-up")
        else:
            exp.append("⚠ High provisional onboarding complexity — deeper study expected")

        return exp
