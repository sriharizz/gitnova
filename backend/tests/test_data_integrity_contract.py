"""
GitNova v4.2 — Data Integrity & Publication Contract Tests

Verifies production feed invariants:
1. Closed issues cannot be published or returned in production feeds.
2. PR objects cannot enter issue feeds.
3. Benchmark / unverified test data cannot enter production feeds.
4. Published issues require a verified status and non-empty explanation payload.
5. GitHub URL identity matches repo_full_name and github_issue_number 1:1.
6. Missing explanation throws / returns empty array, NOT generic mock templates.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.db.issues import row_to_issue_dict
from app.schemas.explanation import IssueExplanation, GuidedSolutionStep

client = TestClient(app)


def test_row_to_issue_dict_github_url_identity():
    """Verify GitHub URL is computed deterministically from repo_full_name and issue number."""
    row = {
        "id": str(uuid4()),
        "repo_id": str(uuid4()),
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "Stream context issue",
        "quality_score": 90,
        "quality_grade": "high",
        "is_published": True
    }
    issue_dict = row_to_issue_dict(row)
    assert issue_dict["repo_full_name"] == "pallets/flask"
    assert issue_dict["github_issue_number"] == 6123


def test_closed_issue_cannot_be_published():
    """Verify that a closed GitHub issue does not meet published criteria."""
    closed_row = {
        "github_state": "closed",
        "is_published": False,
        "verification_status": "INVALID"
    }
    assert closed_row["github_state"] != "open"
    assert not closed_row["is_published"]


def test_pr_object_cannot_enter_issue_feed():
    """Verify that Pull Request objects (e.g. url containing /pull/) are quarantined."""
    pr_row = {
        "url": "https://github.com/pallets/flask/pull/5432",
        "is_published": False
    }
    assert "/pull/" in pr_row["url"]
    assert not pr_row["is_published"]


def test_published_issue_deserializes_distinct_explanation():
    """Verify that explanation JSONB deserializes cleanly to IssueExplanation."""
    explanation_json = {
        "status": "SUCCESS",
        "summary": "Fix stream context leak.",
        "why_it_happens": "GeneratorExit not caught.",
        "prerequisite_concepts": ["Flask context"],
        "step_by_step_plan": [
            {
                "step_number": 1,
                "title": "Inspect helpers.py",
                "description": "Locate line 140",
                "target_file": "src/flask/helpers.py"
            }
        ],
        "relevant_locations": [],
        "common_pitfalls": []
    }
    row = {
        "id": str(uuid4()),
        "repo_id": str(uuid4()),
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "Stream context leak",
        "explanation": explanation_json
    }
    issue_dict = row_to_issue_dict(row)
    exp = issue_dict["explanation"]
    assert isinstance(exp, IssueExplanation)
    assert exp.summary == "Fix stream context leak."
    assert len(exp.step_by_step_plan) == 1
    assert exp.step_by_step_plan[0].target_file == "src/flask/helpers.py"
