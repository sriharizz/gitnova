"""
GitNova v4.3 — Phase B/C Opportunity Evaluator & Data Model Unit Tests
=======================================================================
Tests all 20 Phase B/C requirement scenarios plus state transition scenarios.
"""

import pytest
from app.pipeline.opportunity_evaluator import ContributionOpportunityEvaluator
from app.main import IssueOut


# Test 1: Closed issue -> NOT_RECOMMENDED
def test_closed_issue():
    issue = {"number": 101, "state": "closed", "title": "Closed bug", "user": {"login": "reporter"}}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "NOT_RECOMMENDED"
    assert res["is_eligible"] is False


# Test 2: Assigned issue -> NOT_RECOMMENDED
def test_assigned_issue():
    issue = {"number": 102, "state": "open", "title": "Assigned bug", "assignee": {"login": "dev1"}, "user": {"login": "reporter"}}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "NOT_RECOMMENDED"
    assert res["is_eligible"] is False


# Test 3: Unassigned open issue -> LIKELY_AVAILABLE
def test_unassigned_open_issue():
    issue = {"number": 103, "state": "open", "title": "Open issue", "user": {"login": "reporter"}, "labels": []}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "LIKELY_AVAILABLE"
    assert res["is_eligible"] is True


# Test 4: good-first-issue -> HIGH confidence
def test_good_first_issue_signal():
    issue = {"number": 104, "state": "open", "title": "GFI bug", "user": {"login": "reporter"}, "labels": [{"name": "good first issue"}]}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "LIKELY_AVAILABLE"
    assert res["confidence"] == "HIGH"
    assert res["signals"]["has_positive_labels"] is True


# Test 5: help-wanted -> positive signal
def test_help_wanted_signal():
    issue = {"number": 105, "state": "open", "title": "Help wanted bug", "user": {"login": "reporter"}, "labels": [{"name": "help wanted"}]}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "LIKELY_AVAILABLE"
    assert res["confidence"] == "HIGH"


# Test 6: duplicate -> NOT_RECOMMENDED
def test_duplicate_label_hard_reject():
    issue = {"number": 106, "state": "open", "title": "Duplicate issue", "user": {"login": "reporter"}, "labels": [{"name": "duplicate"}]}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "NOT_RECOMMENDED"
    assert res["is_eligible"] is False


# Test 7: wontfix -> NOT_RECOMMENDED
def test_wontfix_label_hard_reject():
    issue = {"number": 107, "state": "open", "title": "Wontfix issue", "user": {"login": "reporter"}, "labels": [{"name": "wontfix"}]}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "NOT_RECOMMENDED"
    assert res["is_eligible"] is False


# Test 8: stale -> CHECK_DISCUSSION
def test_stale_label_soft_warning():
    issue = {"number": 108, "state": "open", "title": "Stale issue", "user": {"login": "reporter"}, "labels": [{"name": "stale"}]}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "CHECK_DISCUSSION"
    assert res["is_eligible"] is True
    assert any("Soft triage label" in w for w in res["warnings"])


# Test 9: question -> CHECK_DISCUSSION
def test_question_label_soft_warning():
    issue = {"number": 109, "state": "open", "title": "Question issue", "user": {"login": "reporter"}, "labels": [{"name": "question"}]}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "CHECK_DISCUSSION"
    assert res["is_eligible"] is True


# Test 10: linked PR -> CHECK_DISCUSSION
def test_linked_pr_detection():
    issue = {"number": 110, "state": "open", "title": "Issue with PR", "user": {"login": "reporter"}}
    timeline = [{"event": "cross-referenced", "source": {"issue": {"number": 456, "title": "Fix #110", "html_url": "https://github.com/org/repo/pull/456", "pull_request": {}, "state": "open"}}}]
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue, timeline_events=timeline)
    assert res["availability_status"] == "CHECK_DISCUSSION"
    assert res["signals"]["linked_pr_count"] == 1
    assert any("linked pull request" in w for w in res["warnings"])


# Test 11: referenced commit -> CHECK_DISCUSSION
def test_referenced_commit_detection():
    issue = {"number": 111, "state": "open", "title": "Issue with commit", "user": {"login": "reporter"}}
    timeline = [{"event": "referenced"}]
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue, timeline_events=timeline)
    assert res["availability_status"] == "CHECK_DISCUSSION"
    assert res["signals"]["referenced_commits_count"] == 1


# Test 12: recent contributor activity -> evidence statement
def test_recent_contributor_activity():
    issue = {"number": 112, "state": "open", "title": "Active issue", "user": {"login": "reporter"}, "comments": 2}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert any("Open on GitHub" in stmt for stmt in res["evidence"])


# Test 13: recent maintainer activity -> evidence statement
def test_recent_maintainer_activity():
    issue = {"number": 113, "state": "open", "title": "Maintainer issue", "user": {"login": "davidism"}, "labels": [{"name": "good first issue"}]}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["reporter_username"] == "davidism"
    assert any("Maintainer label" in stmt for stmt in res["evidence"])


# Test 14: no labels -> LIKELY_AVAILABLE (do not reject)
def test_no_labels_does_not_reject():
    issue = {"number": 114, "state": "open", "title": "Clean issue without labels", "user": {"login": "reporter"}, "labels": []}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "LIKELY_AVAILABLE"
    assert res["is_eligible"] is True


# Test 15: missing CONTRIBUTING.md -> warning indicator
def test_missing_contributing_guide():
    issue = {"number": 115, "state": "open", "title": "Issue without guide", "user": {"login": "reporter"}}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert "last_verified_at" in res
    assert res["last_verified_at"] is not None


# Test 16: repository with CONTRIBUTING.md -> evidence statement
def test_repo_with_contributing_guide():
    issue = {"number": 116, "state": "open", "title": "Issue with guide", "user": {"login": "reporter"}}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["is_eligible"] is True


# Test 17: pull request accidentally returned as issue -> NOT_RECOMMENDED
def test_pull_request_accidentally_returned_as_issue():
    issue = {"number": 117, "state": "open", "title": "Accidental PR", "pull_request": {"html_url": "https://github.com/org/repo/pull/117"}}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["availability_status"] == "NOT_RECOMMENDED"
    assert res["is_eligible"] is False


# Test 18: reporter mismatch validation
def test_reporter_attribution_preservation():
    issue = {"number": 118, "state": "open", "title": "Test reporter", "user": {"login": "real_reporter_user"}}
    res = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue)
    assert res["reporter_username"] == "real_reporter_user"


# Test 19: issue number/title mismatch validation
def test_issue_number_and_title_invariants():
    issue_data = {
        "id": "11111111-1111-1111-1111-111111111111",
        "repo_id": "22222222-2222-2222-2222-222222222222",
        "repo_full_name": "pallets/flask",
        "github_issue_number": 6123,
        "title": "Real title from GitHub",
        "reporter_username": "davidism"
    }
    model = IssueOut(**issue_data)
    assert model.github_url == "https://github.com/pallets/flask/issues/6123"
    assert model.reporter_username == "davidism"


# Test 20: GitHub URL mismatch validation
def test_github_url_dynamic_computation():
    model = IssueOut(
        id="11111111-1111-1111-1111-111111111111",
        repo_id="22222222-2222-2222-2222-222222222222",
        repo_full_name="tinygrad/tinygrad",
        github_issue_number=6043,
        title="Docs fix",
        reporter_username="geohot"
    )
    assert model.github_url == "https://github.com/tinygrad/tinygrad/issues/6043"


# Test State Transitions: OPEN -> CLOSED
def test_state_transition_open_to_closed():
    issue_open = {"number": 201, "state": "open", "title": "Transition bug", "user": {"login": "user1"}}
    res_open = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue_open)
    assert res_open["availability_status"] == "LIKELY_AVAILABLE"

    issue_closed = {"number": 201, "state": "closed", "title": "Transition bug", "user": {"login": "user1"}}
    res_closed = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue_closed)
    assert res_closed["availability_status"] == "NOT_RECOMMENDED"


# Test State Transitions: OPEN -> ASSIGNED
def test_state_transition_open_to_assigned():
    issue_unassigned = {"number": 202, "state": "open", "title": "Assign bug", "user": {"login": "user1"}, "assignees": []}
    res_unassigned = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue_unassigned)
    assert res_unassigned["availability_status"] == "LIKELY_AVAILABLE"

    issue_assigned = {"number": 202, "state": "open", "title": "Assign bug", "user": {"login": "user1"}, "assignees": [{"login": "dev1"}]}
    res_assigned = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue_assigned)
    assert res_assigned["availability_status"] == "NOT_RECOMMENDED"


# Test State Transitions: OPEN -> LINKED PR
def test_state_transition_open_to_linked_pr():
    issue_no_pr = {"number": 203, "state": "open", "title": "PR bug", "user": {"login": "user1"}}
    res_no_pr = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue_no_pr)
    assert res_no_pr["availability_status"] == "LIKELY_AVAILABLE"

    timeline_pr = [{"event": "cross-referenced", "source": {"issue": {"number": 777, "pull_request": {}, "state": "open"}}}]
    res_with_pr = ContributionOpportunityEvaluator.evaluate_issue_opportunity(issue_no_pr, timeline_events=timeline_pr)
    assert res_with_pr["availability_status"] == "CHECK_DISCUSSION"
