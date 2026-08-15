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
