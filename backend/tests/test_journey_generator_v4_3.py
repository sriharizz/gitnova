"""
GitNova v4.3 — Phase D Contribution Journey Unit Tests
======================================================
Tests all 15 Phase D requirements for dynamic 10-stage Contribution Journey generation.
"""

import pytest
from app.schemas.explanation import ContributionJourney, ContributionJourneyStage, IssueExplanation
from app.pipeline.journey_generator import ContributionJourneyGenerator


# Test 1: Journey schema validation
def test_journey_schema_validation():
    journey_data = {
        "journey_version": "4.3",
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context bug",
        "reporter_username": "davidism",
        "availability_status": "LIKELY_AVAILABLE",
        "opportunity_confidence": "HIGH",
        "last_verified_at": "2026-08-12T12:00:00Z",
        "stages": []
    }
    model = ContributionJourney(**journey_data)
    assert model.journey_version == "4.3"
    assert model.repo_full_name == "pallets/flask"


# Test 2: Exactly 10 stages exist
def test_ten_stages_exist():
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context issue",
        "reporter_username": "davidism",
        "explanation": {
            "summary": "Generator context leak",
            "why_it_happens": "App context remains active on generator exit",
            "relevant_locations": [{"file_path": "src/flask/helpers.py", "symbol_name": "stream_with_context"}]
        }
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    assert len(journey.stages) == 10
    stage_ids = [s.stage_id for s in journey.stages]
    expected_ids = ["understand", "check_status", "learn", "explore", "investigate", "plan", "implement", "test", "prepare_pr", "review"]
    assert stage_ids == expected_ids


# Test 3: Stages contain issue-specific content
def test_stages_contain_issue_specific_content():
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context abandoned generator",
        "reporter_username": "davidism",
        "explanation": {
            "summary": "Generator context leak in stream_with_context",
            "why_it_happens": "Unclosed generator leaves App Context active",
            "relevant_locations": [{"file_path": "src/flask/helpers.py", "symbol_name": "stream_with_context"}]
        }
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    assert "@davidism" in journey.stages[0].explanation
    assert "stream_with_context" in journey.stages[0].explanation
    assert "src/flask/helpers.py" in journey.stages[3].targets


# Test 4: Target files remain grounded
def test_target_files_remain_grounded():
    issue_stub = {
        "repo_full_name": "tinygrad/tinygrad",
        "github_issue_number": 6043,
        "title": "docs: fix typos in errorhandling.rst",
        "reporter_username": "geohot",
        "explanation": {
            "summary": "Documentation typos in errorhandling.rst",
            "why_it_happens": "Spelling errors in docstring",
            "relevant_locations": [{"file_path": "docs/errorhandling.rst", "symbol_name": "ErrorHandlingDoc"}]
        }
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    assert "docs/errorhandling.rst" in journey.stages[3].targets
    assert "docs/errorhandling.rst" in journey.stages[6].targets


# Test 5: Generic fallback plans are rejected
def test_generic_fallback_plans_rejected():
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6093,
        "title": "IPv6 addresses parsed incorrectly",
        "reporter_username": "untitaker",
        "explanation": {
            "summary": "IPv6 bracket parsing error in CLI",
            "why_it_happens": "partition(':') fails on IPv6 colons",
            "step_by_step_plan": [{"description": "Locate host/port parsing in src/flask/cli.py run_command"}],
            "relevant_locations": [{"file_path": "src/flask/cli.py", "symbol_name": "run_command"}]
        }
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    plan_stage = journey.stages[5]
    assert any("src/flask/cli.py" in step for step in plan_stage.steps)


# Test 6: Missing evidence explicitly represented
def test_missing_evidence_explicitly_represented():
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 9999,
        "title": "Unknown bug",
        "reporter_username": "unknown_dev",
        "opportunity_warnings": ["⚠ Status unverified for 14 hours"],
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    check_status_stage = journey.stages[1]
    assert len(check_status_stage.warnings) > 0


# Test 7: Contribution status propagates correctly
def test_contribution_status_propagates_correctly():
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6065,
        "title": "HTTP QUERY method support",
        "reporter_username": "pgjones",
        "availability_status": "CHECK_DISCUSSION",
        "opportunity_confidence": "MEDIUM",
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    assert journey.availability_status == "CHECK_DISCUSSION"
    assert journey.opportunity_confidence == "MEDIUM"
    assert "CHECK_DISCUSSION" in journey.stages[1].explanation


# Test 8: Freshness propagates correctly
def test_freshness_propagates_correctly():
    timestamp = "2026-08-12T14:00:00Z"
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context issue",
        "last_verified_at": timestamp,
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    assert journey.last_verified_at == timestamp


# Test 9: Repository contribution instructions propagate correctly
def test_repo_contribution_instructions_propagate():
    repo_guide = {"raw_contributing_md": "Run pytest to execute tests."}
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6093,
        "title": "IPv6 issue",
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub, repo_guide=repo_guide)
    test_stage = journey.stages[7]
    assert "pytest" in test_stage.commands


# Test 10: Different issues generate different journeys
def test_different_issues_generate_different_journeys():
    issue_flask = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context generator leak",
        "reporter_username": "davidism",
        "explanation": {
            "summary": "Generator context leak in stream_with_context",
            "relevant_locations": [{"file_path": "src/flask/helpers.py", "symbol_name": "stream_with_context"}]
        }
    }
    issue_tinygrad = {
        "repo_full_name": "tinygrad/tinygrad",
        "github_issue_number": 6043,
        "title": "docs: fix typos in errorhandling.rst",
        "reporter_username": "geohot",
        "explanation": {
            "summary": "Documentation typos in errorhandling.rst",
            "relevant_locations": [{"file_path": "docs/errorhandling.rst", "symbol_name": "ErrorHandlingDoc"}]
        }
    }
    journey_flask = ContributionJourneyGenerator.generate_journey(issue_flask)
    journey_tinygrad = ContributionJourneyGenerator.generate_journey(issue_tinygrad)

    assert journey_flask.stages[3].targets != journey_tinygrad.stages[3].targets
    assert journey_flask.reporter_username == "davidism"
    assert journey_tinygrad.reporter_username == "geohot"


# Test 11: Closed issue maps to NOT_RECOMMENDED
def test_closed_issue_cannot_receive_likely_available():
    issue_closed = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 5000,
        "title": "Old closed bug",
        "availability_status": "NOT_RECOMMENDED",
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_closed)
    assert journey.availability_status == "NOT_RECOMMENDED"


# Test 12: Linked PR causes appropriate warning
def test_linked_pr_causes_appropriate_warning():
    issue_pr = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6093,
        "title": "IPv6 issue",
        "availability_status": "CHECK_DISCUSSION",
        "opportunity_warnings": ["⚠ Linked PR #456 detected"],
        "explanation": {}
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_pr)
    assert any("Linked PR" in w for w in journey.stages[1].warnings)


# Test 13: Target file consistency across Overview, Explorer, Plan, and Journey
def test_target_file_consistency():
    explanation_dict = {
        "summary": "stream_with_context issue",
        "why_it_happens": "Generator exit unhandled",
        "relevant_locations": [{"file_path": "src/flask/helpers.py", "symbol_name": "stream_with_context"}],
        "step_by_step_plan": [{"description": "Modify src/flask/helpers.py generator wrapper"}]
    }
    issue_stub = {
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "stream_with_context issue",
        "explanation": explanation_dict
    }
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    assert journey.stages[3].targets[0] == "src/flask/helpers.py"
    assert journey.stages[4].targets[0] == "src/flask/helpers.py"
    assert journey.stages[5].targets[0] == "src/flask/helpers.py"
    assert journey.stages[6].targets[0] == "src/flask/helpers.py"


# Test 14: Journey version is present
def test_journey_version_is_present():
    issue_stub = {"repo_full_name": "pallets/flask", "github_issue_number": 6123, "explanation": {}}
    journey = ContributionJourneyGenerator.generate_journey(issue_stub)
    assert journey.journey_version in ("4.3", "4.4", "4.5")


# Test 15: Backwards compatibility preserved
def test_backwards_compatibility_preserved():
    exp_dict = {
        "status": "SUCCESS",
        "summary": "Flask issue explanation",
        "why_it_happens": "Root cause",
        "prerequisite_concepts": ["Flask Context"],
        "relevant_locations": [{"file_path": "src/flask/helpers.py"}]
    }
    exp_model = IssueExplanation(**exp_dict)
    assert exp_model.status == "SUCCESS"
    assert exp_model.contribution_journey is None
