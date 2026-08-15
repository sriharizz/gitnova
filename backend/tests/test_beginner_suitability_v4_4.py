"""
GitNova v4.4 — Unit Tests for Beginner Suitability, Structured Diagrams, and Provenance Models
"""

import pytest
from app.schemas.explanation import (
    BeginnerSuitability,
    RepositoryComplexity,
    ContributionComplexity,
    SetupComplexity,
    ContributionType,
    ProvenanceType,
    ProvenanceItem,
    StructuredDiagram,
    DiscussionSummary,
    FreshnessMetadata
)
from app.pipeline.opportunity_evaluator import ContributionOpportunityEvaluator
from app.pipeline.journey_generator import ContributionJourneyGenerator


class TestBeginnerSuitabilityEvaluation:
    """Tests for multi-dimensional contribution complexity and explainable suitability scoring."""

    def test_documentation_issue_suitability(self):
        raw_issue = {
            "title": "docs: fix typos in errorhandling.rst",
            "body": "Fix typo in sphinx documentation",
            "repo_name": "tinygrad/tinygrad"
        }
        suitability = ContributionOpportunityEvaluator.evaluate_beginner_suitability(
            raw_issue=raw_issue,
            retrieved_locations=[{"file_path": "docs/errorhandling.rst"}],
            has_positive_labels=True
        )
        assert suitability.contribution_type == ContributionType.DOCUMENTATION
        assert suitability.contribution_complexity == ContributionComplexity.BEGINNER
        assert suitability.score >= 90
        assert any("Documentation-only" in s for s in suitability.positive_signals)

    def test_flask_6123_generator_exception_suitability(self):
        raw_issue = {
            "title": "`stream_with_context`: abandoned generator leaves the app context current on the worker thread",
            "body": "GeneratorExit exception handling",
            "repo_name": "pallets/flask"
        }
        suitability = ContributionOpportunityEvaluator.evaluate_beginner_suitability(
            raw_issue=raw_issue,
            retrieved_locations=[{"file_path": "src/flask/helpers.py"}],
            has_positive_labels=True
        )
        assert suitability.contribution_type == ContributionType.BUG_FIX
        assert suitability.contribution_complexity == ContributionComplexity.BEGINNER_PLUS
        assert suitability.score == 72
        assert any("GeneratorExit" in s for s in suitability.warning_signals)
        assert any("Concurrency hazard" in s for s in suitability.warning_signals)

    def test_small_feature_query_method_suitability(self):
        raw_issue = {
            "title": "Add a query() route shortcut and MethodView support for HTTP QUERY",
            "body": "RFC 10008 query decorator",
            "repo_name": "pallets/flask"
        }
        suitability = ContributionOpportunityEvaluator.evaluate_beginner_suitability(
            raw_issue=raw_issue,
            retrieved_locations=[{"file_path": "src/flask/app.py"}, {"file_path": "src/flask/views.py"}],
            has_positive_labels=True
        )
        assert suitability.contribution_type == ContributionType.SMALL_FEATURE
        assert suitability.contribution_complexity == ContributionComplexity.INTERMEDIATE
        assert suitability.score == 76


class TestStructuredDiagramsAndProvenance:
    """Tests for deterministic structured diagram generation and provenance tracking."""

    def test_journey_generates_diagrams(self):
        issue_stub = {
            "repo_full_name": "pallets/flask",
            "github_issue_number": 6123,
            "title": "`stream_with_context`: abandoned generator leaves app context current",
            "reporter_username": "davidism",
            "availability_status": "LIKELY_AVAILABLE",
            "explanation": {
                "summary": "Abandoned generator leaves Flask app context active on worker thread.",
                "why_it_happens": "stream_with_context decorates generator functions but does not catch GeneratorExit.",
                "relevant_locations": [
                    {
                        "file_path": "src/flask/helpers.py",
                        "symbol_name": "stream_with_context",
                        "lines": "140-185",
                        "role": "Streaming Context Decorator"
                    }
                ],
                "step_by_step_plan": [
                    {"step_number": 1, "title": "Locate stream_with_context", "description": "Open src/flask/helpers.py"}
                ]
            }
        }
        journey = ContributionJourneyGenerator.generate_journey(issue_stub)
        assert journey.journey_version in ("4.4", "4.5")
        assert journey.beginner_suitability is not None
        assert journey.beginner_suitability.score == 72
        assert journey.freshness is not None

        # Check Stage 4 diagrams (Code Relationship)
        stage4 = next(s for s in journey.stages if s.stage_id == "explore")
        assert len(stage4.diagrams) == 1
        assert stage4.diagrams[0].diagram_type == "CODE_RELATIONSHIP"
        assert len(stage4.diagrams[0].nodes) == 4
        assert stage4.diagrams[0].nodes[0].provenance.provenance_type == ProvenanceType.VERIFIED_FACT

        # Check Stage 5 diagrams (Failure Flow and Expected vs Current)
        stage5 = next(s for s in journey.stages if s.stage_id == "investigate")
        assert len(stage5.diagrams) == 2
        assert stage5.diagrams[0].diagram_type == "FAILURE_FLOW"
        assert len(stage5.diagrams[0].nodes) == 4
        assert stage5.diagrams[1].diagram_type == "EXPECTED_VS_CURRENT"
