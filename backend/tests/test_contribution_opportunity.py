"""
GitNova v4.2 — Contribution Opportunity Evaluator & Data Contract Unit Tests
==============================================================================
Validates opportunity signals, hard vs soft triage label handling, reporter attribution,
and structured beginner concept card deserialization.
"""

import pytest
from app.pipeline.opportunity_evaluator import ContributionOpportunityEvaluator
from app.schemas.explanation import IssueExplanation, ConceptDetail


def test_open_unassigned_positive_issue_evaluation():
    raw_issue = {
        "number": 6123,
        "state": "open",
        "title": "Add stream_with_context teardown",
        "body": "Detailed reproduction steps for Flask app context teardown issue...",
        "user": {"login": "davidism"},
        "assignee": None,
        "assignees": [],
        "labels": [{"name": "good first issue"}],
        "comments": 3
    }
    eval_res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue)

    assert eval_res["is_eligible"] is True
    assert eval_res["opportunity_confidence"] == "HIGH"
    assert eval_res["reporter_username"] == "davidism"
    assert eval_res["rejection_reason"] is None
    assert "✓ Open on GitHub" in eval_res["signals"]["evidence_statements"]
    assert "✓ Unassigned on GitHub" in eval_res["signals"]["evidence_statements"]


def test_assigned_issue_rejection():
    raw_issue = {
        "number": 5000,
        "state": "open",
        "title": "Some feature",
        "user": {"login": "contributor1"},
        "assignee": {"login": "assigned_dev"},
        "assignees": [{"login": "assigned_dev"}],
        "labels": [],
        "comments": 0
    }
    eval_res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue)

    assert eval_res["is_eligible"] is False
    assert eval_res["availability_status"] == "NOT_RECOMMENDED"
    assert eval_res["confidence"] == "LOW"
    assert "assigned" in eval_res["rejection_reason"].lower()


def test_hard_rejection_labels():
    raw_issue = {
        "number": 4000,
        "state": "open",
        "title": "Bug report",
        "user": {"login": "reporter"},
        "assignees": [],
        "labels": [{"name": "wontfix"}],
        "comments": 1
    }
    eval_res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue)

    assert eval_res["is_eligible"] is False
    assert eval_res["availability_status"] == "NOT_RECOMMENDED"
    assert eval_res["confidence"] == "LOW"
    assert "hard rejection label" in eval_res["rejection_reason"].lower()


def test_soft_warning_labels_do_not_hard_reject():
    raw_issue = {
        "number": 3000,
        "state": "open",
        "title": "Question about routing",
        "user": {"login": "questioner"},
        "assignees": [],
        "labels": [{"name": "stale"}, {"name": "question"}],
        "comments": 5
    }
    eval_res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(raw_issue)

    # Soft labels do NOT hard reject — they downgrade availability_status to CHECK_DISCUSSION!
    assert eval_res["is_eligible"] is True
    assert eval_res["availability_status"] == "CHECK_DISCUSSION"
    assert eval_res["confidence"] == "MEDIUM"
    assert eval_res["reporter_username"] == "questioner"
    assert any("Soft triage label" in stmt for stmt in eval_res["warnings"])


def test_structured_concept_cards_deserialization():
    explanation_data = {
        "status": "SUCCESS",
        "summary": "Flask stream_with_context issue explanation",
        "why_it_happens": "Unclosed generator leaves App Context current",
        "prerequisite_concepts": ["Flask App Context"],
        "structured_concepts": [
            {
                "concept_name": "Flask App Context",
                "short_explanation": "Flask's application-level state container.",
                "why_it_matters": "Prevents state pollution across threads.",
                "connection_to_issue": "Fails to pop when generator terminates early."
            }
        ],
        "step_by_step_plan": [
            {
                "step_number": 1,
                "title": "Inspect helper.py",
                "description": "Locate stream_with_context around line 140",
                "target_file": "src/flask/helpers.py"
            }
        ],
        "relevant_locations": [
            {
                "file_path": "src/flask/helpers.py",
                "symbol_name": "stream_with_context",
                "lines": "140-185",
                "role": "Decorator",
                "is_verified": True
            }
        ]
    }

    explanation_obj = IssueExplanation(**explanation_data)
    assert len(explanation_obj.structured_concepts) == 1
    concept = explanation_obj.structured_concepts[0]
    assert concept.concept_name == "Flask App Context"
    assert concept.why_it_matters == "Prevents state pollution across threads."
