"""
GitNova v4.2 — Sprint 8 Step 1 Issue Explainer Unit Tests

Tests for:
  - Pluggable LLM provider abstraction & factory
  - IssueExplanation Pydantic schema validation & serialization
  - INSUFFICIENT_EVIDENCE short-circuiting (zero LLM calls on thin context)
  - Programmatic GroundingVerifier (file citation validation & hallucinated path pruning)
"""

from unittest.mock import MagicMock, patch
import pytest
from pydantic import BaseModel

from app.clients.llm.base import BaseLLMProvider
from app.clients.llm.groq import GroqProvider
from app.clients.llm.factory import LLMProviderFactory
from app.pipeline.grounding_verifier import GroundingVerifier
from app.pipeline.issue_explainer import generate_issue_explanation, format_grounded_prompt
from app.schemas.explanation import (
    IssueExplanation,
    GroundedCodeLocation,
    GuidedSolutionStep
)


# ── Mock LLM Provider for Testing ─────────────────────────────────────────────

class MockLLMProvider(BaseLLMProvider):
    def __init__(self, response_instance: BaseModel = None):
        self.response_instance = response_instance
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-model-v1"

    def generate_structured(self, prompt: str, schema: type) -> BaseModel:
        self.call_count += 1
        if self.response_instance:
            return self.response_instance
        
        return IssueExplanation(
            status="SUCCESS",
            summary="Mock summary",
            why_it_happens="Mock cause",
            prerequisite_concepts=["Mock Prereq"],
            step_by_step_plan=[
                GuidedSolutionStep(step_number=1, title="Step 1", description="Fix code", target_file="src/app.py")
            ],
            relevant_locations=[
                GroundedCodeLocation(file_path="src/app.py", symbol_name="main", lines="1-10", role="Main entry")
            ],
            common_pitfalls=["Avoid null check errors"]
        )


# ── Provider & Factory Unit Tests ──────────────────────────────────────────────

class TestLLMProviderAbstraction:

    def test_factory_returns_configured_provider(self):
        provider = LLMProviderFactory.get_provider("gemini")
        assert provider.provider_name == "gemini"
        assert "gemini" in provider.model_name.lower()

        groq_provider = LLMProviderFactory.get_provider("groq")
        assert groq_provider.provider_name == "groq"

    def test_mock_provider_conforms_to_interface(self):
        provider = MockLLMProvider()
        assert provider.provider_name == "mock"
        assert provider.model_name == "mock-model-v1"
        res = provider.generate_structured("prompt", IssueExplanation)
        assert isinstance(res, IssueExplanation)
        assert provider.call_count == 1

    def test_groq_provider_uses_configured_llm_model(self):
        provider = GroqProvider(api_key="dummy_key", model="llama-3.3-70b-versatile")
        assert provider.model_name == "llama-3.3-70b-versatile"

        default_provider = GroqProvider(api_key="dummy_key")
        assert default_provider.model_name == "llama-3.3-70b-versatile"

    def test_groq_provider_sanitizes_api_key_on_error(self):
        fake_secret_key = "secret_key_99999"
        provider = GroqProvider(api_key=fake_secret_key, model="openai/gpt-oss-120b")

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = f"Invalid API Key: {fake_secret_key}"

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(RuntimeError) as exc_info:
                provider.generate_structured("prompt", IssueExplanation)
            
            err_msg = str(exc_info.value)
            assert fake_secret_key not in err_msg
            assert "[REDACTED]" in err_msg


# ── Schema Validation & Serialization Tests ────────────────────────────────────

class TestIssueExplanationSchema:

    def test_issue_explanation_defaults_and_serialization(self):
        exp = IssueExplanation(
            summary="Bug in flag parsing",
            why_it_happens="Null check missing in start.js",
            prerequisite_concepts=["Commander CLI", "Fastify options"],
            step_by_step_plan=[
                GuidedSolutionStep(step_number=1, title="Add null check", description="Check if options is undefined")
            ],
            relevant_locations=[
                GroundedCodeLocation(file_path="start.js", symbol_name="parseOptions", lines="40-50")
            ]
        )

        assert exp.status == "SUCCESS"
        assert len(exp.relevant_locations) == 1
        assert exp.relevant_locations[0].is_verified is False  # Set to True by verifier later

        json_data = exp.model_dump()
        assert json_data["summary"] == "Bug in flag parsing"
        assert json_data["relevant_locations"][0]["file_path"] == "start.js"


# ── Grounding Verifier & Anti-Hallucination Tests ──────────────────────────────

class TestGroundingVerifier:

    def test_verifier_validates_retrieved_files(self):
        retrieved_chunks = [
            {"file_path": "src/auth.py", "qualified_symbol_name": "AuthManager.login", "content": "def login(): pass\n" * 10},
            {"file_path": "src/user.py", "qualified_symbol_name": "User.get", "content": "def get(): pass\n" * 10},
        ]

        exp = IssueExplanation(
            summary="Auth issue",
            why_it_happens="Invalid token",
            relevant_locations=[
                GroundedCodeLocation(file_path="src/auth.py", symbol_name="AuthManager.login", lines="1-10"),
                GroundedCodeLocation(file_path="src/fake_file.py", symbol_name="Fake.method", lines="1-10")  # Hallucinated!
            ]
        )

        verifier = GroundingVerifier(retrieved_chunks)
        validated = verifier.verify_and_sanitize(exp)

        # src/fake_file.py should be pruned
        assert len(validated.relevant_locations) == 1
        assert validated.relevant_locations[0].file_path == "src/auth.py"
        assert validated.relevant_locations[0].is_verified is True
        assert "unverified file citations were automatically pruned" in validated.disclaimer

    def test_verifier_calculates_total_tokens(self):
        chunks = [
            {"content": "word " * 40},  # ~50 tokens
            {"content": "word " * 40},  # ~50 tokens
        ]
        tokens = GroundingVerifier.calculate_total_tokens(chunks)
        assert tokens == 100

    def test_is_evidence_insufficient_returns_true_for_thin_context(self):
        thin_chunks = [{"content": "short text"}]  # ~2 tokens
        assert GroundingVerifier.is_evidence_insufficient(thin_chunks, min_token_threshold=100) is True
        assert GroundingVerifier.is_evidence_insufficient([], min_token_threshold=100) is True

    def test_is_evidence_insufficient_returns_false_for_rich_context(self):
        rich_chunks = [{"content": "def main():\n    pass\n" * 20}]  # ~120 tokens
        assert GroundingVerifier.is_evidence_insufficient(rich_chunks, min_token_threshold=100) is False


# ── Pipeline Orchestrator & Short-Circuit Tests ───────────────────────────────

class TestIssueExplainerOrchestrator:

    def test_insufficient_evidence_short_circuits_without_llm_call(self):
        mock_provider = MockLLMProvider()
        thin_chunks = [{"content": "tiny snippet"}]

        res = generate_issue_explanation(
            repo_name="fastify/fastify-cli",
            issue_title="Bug in CLI",
            issue_body="Detail",
            retrieved_chunks=thin_chunks,
            provider=mock_provider,
        )

        # Provider call_count must be ZERO because short-circuit triggered
        assert mock_provider.call_count == 0
        assert res.status == "INSUFFICIENT_EVIDENCE"
        assert "insufficient" in res.summary.lower()
        assert len(res.relevant_locations) == 0

    def test_sufficient_evidence_invokes_llm_and_verifier(self):
        mock_provider = MockLLMProvider()
        rich_chunks = [
            {
                "file_path": "src/app.py",
                "qualified_symbol_name": "main",
                "content": "def main():\n    print('hello')\n" * 15,  # ~150 tokens
                "contextual_header": "[File: src/app.py | Function: main]"
            }
        ]

        res = generate_issue_explanation(
            repo_name="fastify/fastify-cli",
            issue_title="Bug in CLI",
            issue_body="Detail",
            retrieved_chunks=rich_chunks,
            provider=mock_provider,
        )

        # Provider executes two-phase reasoning: Investigation + Planning
        assert mock_provider.call_count == 2
        assert res.status == "SUCCESS"
        assert len(res.relevant_locations) == 1
        assert res.relevant_locations[0].file_path == "src/app.py"
        assert res.relevant_locations[0].is_verified is True
