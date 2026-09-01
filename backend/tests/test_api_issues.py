"""
GitNova v4.2 — Sprint 8 Step 2 FastAPI Issue Explanation Endpoint Unit Tests

Tests for:
  - POST /issues/explain endpoint
  - GET /repos/{owner}/{repo}/issues/{issue_number}/explain endpoint
  - Short-circuit fallback behavior on API layer
  - Response model validation against IssueExplanation schema
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.explanation import IssueExplanation, GroundedCodeLocation, GuidedSolutionStep

client = TestClient(app)


class TestIssueExplanationAPIEndpoints:

    def test_explain_issue_post_endpoint_insufficient_evidence(self):
        payload = {
            "repo_name": "unknown/repo",
            "issue_title": "Obscure bug",
            "issue_body": "No code match"
        }
        
        with patch("app.pipeline.code_retriever.retrieve_chunks_for_issue", return_value=("", [])):
            response = client.post("/issues/explain", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "INSUFFICIENT_EVIDENCE"
        assert "summary" in data

    def test_explain_repo_issue_get_endpoint_insufficient_evidence(self):
        with patch("app.pipeline.code_retriever.retrieve_chunks_for_issue", return_value=("", [])):
            response = client.get("/repos/fastify/fastify-cli/issues/42/explain")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "INSUFFICIENT_EVIDENCE"

    def test_explain_issue_post_endpoint_success_with_mocked_llm(self):
        mock_chunks = [
            {
                "chunk_id": "c1",
                "file_path": "start.js",
                "start_line": 1,
                "end_line": 20,
                "content": "function start() {\n  return 42;\n}" * 10,
                "contextual_header": "[File: start.js]",
                "info_class": "SOURCE_CODE"
            }
        ]

        mock_explanation = IssueExplanation(
            status="SUCCESS",
            summary="CLI start flag issue",
            why_it_happens="Missing option handler",
            prerequisite_concepts=["Fastify CLI options"],
            step_by_step_plan=[
                GuidedSolutionStep(step_number=1, title="Add option", description="Update start.js")
            ],
            relevant_locations=[
                GroundedCodeLocation(file_path="start.js", symbol_name="start", lines="1-20", is_verified=True)
            ]
        )

        with patch("app.pipeline.code_retriever.retrieve_chunks_for_issue", return_value=("[File: start.js]", mock_chunks)), \
             patch("app.pipeline.issue_explainer.generate_issue_explanation", return_value=mock_explanation):
            
            payload = {
                "repo_name": "fastify/fastify-cli",
                "issue_title": "start flag bug",
                "issue_body": "Help with start command"
            }
            response = client.post("/issues/explain", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["summary"] == "CLI start flag issue"
        assert data["relevant_locations"][0]["file_path"] == "start.js"
        assert data["relevant_locations"][0]["is_verified"] is True


# ═════════════════════════════════════════════════════════════════════════════
# Phase 5: Recommendation Ranking & Repository Diversity Test Suite
# ═════════════════════════════════════════════════════════════════════════════

import uuid
from app.schemas.explanation import BeginnerSuitability, ContributionComplexity, SetupComplexity


def _make_mock_issue(
    id_str: str,
    repo_name: str,
    title: str,
    language: str,
    topics: list,
    difficulty: str = "BEGINNER",
    setup_complexity: str = "EASY",
    quality_score: int = 80,
    verification_status: str = "VERIFIED",
    availability_status: str = "LIKELY_AVAILABLE"
):
    from app.main import IssueOut
    suit = BeginnerSuitability(
        score=quality_score,
        tier=ContributionComplexity(difficulty),
        contribution_complexity=ContributionComplexity(difficulty),
        setup_complexity=SetupComplexity(setup_complexity)
    )
    exp = IssueExplanation(
        status="SUCCESS" if verification_status == "VERIFIED" else "INSUFFICIENT_EVIDENCE",
        summary=f"Summary for {title}",
        why_it_happens=f"Explanation of {title}",
        step_by_step_plan=[
            GuidedSolutionStep(step_number=1, title="Step 1", description="Inspect code"),
            GuidedSolutionStep(step_number=2, title="Step 2", description="Apply fix"),
            GuidedSolutionStep(step_number=3, title="Step 3", description="Add test")
        ],
        relevant_locations=[
            GroundedCodeLocation(file_path="src/main.py", symbol_name="run", lines="1-10", is_verified=True)
        ]
    )
    valid_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, id_str)
    return IssueOut(
        id=valid_uuid,
        repo_id=uuid.uuid5(uuid.NAMESPACE_DNS, repo_name),
        repo_full_name=repo_name,
        github_issue_number=1,
        title=title,
        repo_language=language,
        domain_topics=topics,
        quality_score=quality_score,
        difficulty=difficulty,
        difficulty_tier=difficulty,
        verification_status=verification_status,
        availability_status=availability_status,
        beginner_suitability=suit,
        explanation=exp
    )


class TestPhase5RecommendationRankingAndDiversity:

    # 1. Python + AI/ML ranks AI/ML issues above unrelated issues
    def test_python_aiml_ranks_aiml_issues_above_unrelated(self):
        iss_ai = _make_mock_issue("1", "deepset-ai/haystack", "Vector embedding cache bug", "Python", ["nlp", "rag", "transformers"])
        iss_cli = _make_mock_issue("2", "pallets/click", "CLI float argument parsing", "Python", ["cli", "terminal"])
        
        with patch("app.main.list_issues", return_value=[iss_cli, iss_ai]):
            resp = client.get("/recommendations?languages=Python&domains=AI%20%2F%20Machine%20Learning")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["issues"]) == 2
            assert data["issues"][0]["repo_full_name"] == "deepset-ai/haystack"

    # 2. Python + Data ranks data-relevant issues appropriately
    def test_python_data_ranks_data_issues_appropriately(self):
        iss_data = _make_mock_issue("1", "scikit-learn/scikit-learn", "Dataframe column aggregation", "Python", ["data-science", "analytics", "dataframe"])
        iss_cli = _make_mock_issue("2", "pallets/click", "CLI runner command", "Python", ["cli", "terminal"])
        
        with patch("app.main.list_issues", return_value=[iss_cli, iss_data]):
            resp = client.get("/recommendations?languages=Python&domains=Data%20%2F%20Analytics")
            assert resp.status_code == 200
            data = resp.json()
            assert data["issues"][0]["repo_full_name"] == "scikit-learn/scikit-learn"

    # 3. TypeScript + Web ranks web issues
    def test_typescript_web_ranks_web_issues(self):
        iss_web = _make_mock_issue("1", "facebook/docusaurus", "Theme switcher reset bug", "TypeScript", ["react", "web", "frontend"])
        iss_tool = _make_mock_issue("2", "org/ts-parser", "Parser ast node syntax error", "TypeScript", ["compiler", "ast"])
        
        with patch("app.main.list_issues", return_value=[iss_tool, iss_web]):
            resp = client.get("/recommendations?languages=TypeScript,JavaScript&domains=Web%20%2F%20Backend")
            assert resp.status_code == 200
            data = resp.json()
            assert data["issues"][0]["repo_full_name"] == "facebook/docusaurus"

    # 4. Java + Backend ranks Java backend issues
    def test_java_backend_ranks_java_backend_issues(self):
        iss_spring = _make_mock_issue("1", "spring-projects/spring-petclinic", "REST endpoint controller bug", "Java", ["spring", "backend", "api"])
        iss_linter = _make_mock_issue("2", "checkstyle/checkstyle", "Checkstyle AST token rule", "Java", ["ast", "linter"])
        
        with patch("app.main.list_issues", return_value=[iss_linter, iss_spring]):
            resp = client.get("/recommendations?languages=Java&domains=Web%20%2F%20Backend")
            assert resp.status_code == 200
            data = resp.json()
            assert data["issues"][0]["repo_full_name"] == "spring-projects/spring-petclinic"

    # 5. Go + Developer Tools ranks relevant Go tools
    def test_go_devtools_ranks_relevant_go_tools(self):
        iss_cobra = _make_mock_issue("1", "spf13/cobra", "PowerShell autocompletion error", "Go", ["cli", "devtools", "automation"])
        iss_gin = _make_mock_issue("2", "gin-gonic/gin", "HTTP router context timeout", "Go", ["web", "http", "api"])
        
        with patch("app.main.list_issues", return_value=[iss_gin, iss_cobra]):
            resp = client.get("/recommendations?languages=Go&domains=Developer%20Tools%20%2F%20Automation")
            assert resp.status_code == 200
            data = resp.json()
            assert data["issues"][0]["repo_full_name"] == "spf13/cobra"

    # 6. Beginner prefers suitable beginner issues
    def test_beginner_prefers_suitable_beginner_issues(self):
        iss_beg = _make_mock_issue("1", "org/repo1", "Beginner issue", "Python", ["web"], difficulty="BEGINNER")
        iss_adv = _make_mock_issue("2", "org/repo2", "Advanced issue", "Python", ["web"], difficulty="ADVANCED")
        
        with patch("app.main.list_issues", return_value=[iss_beg, iss_adv]):
            resp = client.get("/recommendations?difficulty=BEGINNER")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["issues"]) == 1
            assert data["issues"][0]["id"] == str(uuid.uuid5(uuid.NAMESPACE_DNS, "1"))

    # 7. Very large / HARD setup excluded for beginners
    def test_hard_setup_excluded_for_beginners(self):
        iss_hard = _make_mock_issue("1", "org/repo", "Complex setup bug", "Python", ["web"], setup_complexity="HARD")
        
        with patch("app.main.list_issues", return_value=[iss_hard]):
            resp = client.get("/recommendations?difficulty=BEGINNER")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["issues"]) == 0

    # 8. One repository cannot dominate the response
    def test_one_repository_cannot_dominate_response(self):
        issues = [
            _make_mock_issue(f"a_{i}", "org/dom-repo", f"Dom issue {i}", "Python", ["web"], quality_score=90 - i)
            for i in range(5)
        ] + [
            _make_mock_issue(f"b_{i}", "org/other-repo-1", f"Other 1 issue {i}", "Python", ["web"], quality_score=80 - i)
            for i in range(2)
        ] + [
            _make_mock_issue(f"c_{i}", "org/other-repo-2", f"Other 2 issue {i}", "Python", ["web"], quality_score=75 - i)
            for i in range(2)
        ]
        
        with patch("app.main.list_issues", return_value=issues):
            resp = client.get("/recommendations?languages=Python&limit=10")
            assert resp.status_code == 200
            data = resp.json()
            dom_count = sum(1 for iss in data["issues"] if iss["repo_full_name"] == "org/dom-repo")
            assert dom_count <= 2

    # 9. Maximum 2 issues/repository normally
    def test_maximum_2_issues_per_repository_normally(self):
        issues = [
            _make_mock_issue(f"r1_{i}", "org/repo-1", f"Repo 1 issue {i}", "Python", ["web"])
            for i in range(4)
        ] + [
            _make_mock_issue(f"r2_{i}", "org/repo-2", f"Repo 2 issue {i}", "Python", ["web"])
            for i in range(4)
        ] + [
            _make_mock_issue(f"r3_{i}", "org/repo-3", f"Repo 3 issue {i}", "Python", ["web"])
            for i in range(4)
        ]
        
        with patch("app.main.list_issues", return_value=issues):
            resp = client.get("/recommendations?languages=Python&limit=10")
            assert resp.status_code == 200
            data = resp.json()
            for r_name in ["org/repo-1", "org/repo-2", "org/repo-3"]:
                count = sum(1 for iss in data["issues"] if iss["repo_full_name"] == r_name)
                assert count <= 2

    # 10. Max per repo cap is strictly enforced to 2 even with few repositories
    def test_strict_cap_of_2_issues_when_few_repositories(self):
        issues = [
            _make_mock_issue(f"r1_{i}", "org/only-repo", f"Issue {i}", "Python", ["web"])
            for i in range(5)
        ]
        
        with patch("app.main.list_issues", return_value=issues):
            resp = client.get("/recommendations?languages=Python&limit=5")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["issues"]) == 2

    # 11. Unvalidated issues never reach the response
    def test_unvalidated_issues_never_reach_response(self):
        iss_invalid = _make_mock_issue("1", "org/repo", "Invalid issue", "Python", ["web"], verification_status="INVALID")
        iss_not_rec = _make_mock_issue("2", "org/repo", "Not rec issue", "Python", ["web"], availability_status="NOT_RECOMMENDED")
        
        with patch("app.main.list_issues", return_value=[iss_invalid, iss_not_rec]):
            resp = client.get("/recommendations?languages=Python")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["issues"]) == 0

    # 12. Changing domain changes rankings when relevant candidates differ
    def test_changing_domain_changes_rankings(self):
        iss_ai = _make_mock_issue("1", "org/ai-tool", "Model weight tensor loader", "Python", ["machine-learning", "pytorch"], quality_score=75)
        iss_cli = _make_mock_issue("2", "org/cli-tool", "Argparse subparser completion", "Python", ["cli", "devtools"], quality_score=75)
        
        with patch("app.main.list_issues", return_value=[iss_ai, iss_cli]):
            resp_ai = client.get("/recommendations?languages=Python&domains=AI%20%2F%20Machine%20Learning")
            data_ai = resp_ai.json()
            assert data_ai["issues"][0]["id"] == str(uuid.uuid5(uuid.NAMESPACE_DNS, "1"))

            resp_cli = client.get("/recommendations?languages=Python&domains=Developer%20Tools%20%2F%20Automation")
            data_cli = resp_cli.json()
            assert data_cli["issues"][0]["id"] == str(uuid.uuid5(uuid.NAMESPACE_DNS, "2"))

    # 13. No hardcoded repository/issue identifiers in ranking
    def test_no_hardcoded_identifiers_in_ranking(self):
        iss_new = _make_mock_issue(
            "999",
            "novel-team-xyz/fresh-repo-2026",
            "LLM inference streaming token buffer",
            "Python",
            ["llm", "genai", "agents"]
        )
        with patch("app.main.list_issues", return_value=[iss_new]):
            resp = client.get("/recommendations?languages=Python&domains=AI%20%2F%20Machine%20Learning")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["issues"]) == 1
            assert data["issues"][0]["repo_full_name"] == "novel-team-xyz/fresh-repo-2026"

