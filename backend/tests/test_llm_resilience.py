"""
Unit and Integration Tests for GitNova Ingestion Reliability, LLM Resilience & Concurrency Guard
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel

from app.clients.llm.base import BaseLLMProvider
from app.clients.llm.gemini import GeminiProvider
from app.clients.llm.factory import ResilientLLMProvider
from app.core.lock import IngestionLock, IngestionLockError


class DummySchema(BaseModel):
    summary: str
    status: str


class FailingProvider(BaseLLMProvider):
    def __init__(self, name="failing", model="fail-model", error=RuntimeError("API 429 Rate Limit")):
        self._name = name
        self._model = model
        self._error = error
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def model_name(self) -> str:
        return self._model

    def generate_structured(self, prompt: str, schema: type) -> BaseModel:
        self.call_count += 1
        raise self._error


class WorkingProvider(BaseLLMProvider):
    def __init__(self, name="working", model="work-model"):
        self._name = name
        self._model = model
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def model_name(self) -> str:
        return self._model

    def generate_structured(self, prompt: str, schema: type) -> BaseModel:
        self.call_count += 1
        return DummySchema(summary="Grounded fix summary", status="SUCCESS")


def test_gemini_provider_mocked_success():
    """Verifies GeminiProvider parses valid JSON response into target schema."""
    provider = GeminiProvider(api_key="fake-key", model="gemini-3.6-flash")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '{"summary": "Test summary", "status": "OK"}'}
                    ]
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp):
        res = provider.generate_structured("Test prompt", DummySchema)
        assert isinstance(res, DummySchema)
        assert res.summary == "Test summary"
        assert res.status == "OK"


def test_gemini_provider_bounded_retries_on_429():
    """Verifies GeminiProvider bounds retries on 429 and does not loop infinitely."""
    provider = GeminiProvider(api_key="fake-key", model="gemini-3.5-flash-lite")

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Rate limit exceeded"

    with patch("requests.post", return_value=mock_resp), patch("time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate_structured("Test prompt", DummySchema)
        assert "exhausted all 3 attempts" in str(exc_info.value)
        assert mock_sleep.call_count == 3  # exactly 3 retry sleeps, then bounded failure


def test_resilient_llm_provider_failover():
    """Verifies ResilientLLMProvider cascades to secondary provider when primary fails."""
    primary = FailingProvider(name="failing-primary")
    resilient_provider = ResilientLLMProvider(primary_provider=primary)

    with patch.object(settings_mock := MagicMock(), "groq_api_key", "valid-groq-key"):
        with patch("app.clients.llm.factory.settings", settings_mock):
            with patch("app.clients.llm.factory.GroqProvider") as mock_groq_cls:
                mock_groq_instance = WorkingProvider(name="groq", model="llama-3.3-70b-versatile")
                mock_groq_cls.return_value = mock_groq_instance

                res = resilient_provider.generate_structured("Test prompt", DummySchema)
                assert isinstance(res, DummySchema)
                assert primary.call_count == 1
                assert mock_groq_instance.call_count == 1


def test_ingestion_lock_mutual_exclusion(tmp_path):
    """Verifies IngestionLock prevents duplicate concurrent ingestion runs."""
    lock_file = str(tmp_path / "test_ingestion.lock")

    lock1 = IngestionLock(lock_path=lock_file, timeout_seconds=0)
    lock2 = IngestionLock(lock_path=lock_file, timeout_seconds=0)

    # 1. Lock 1 acquires
    assert lock1.acquire() is True
    assert os.path.exists(lock_file)

    # 2. Lock 2 attempts to acquire -> must raise IngestionLockError
    with pytest.raises(IngestionLockError):
        lock2.acquire()

    # 3. Lock 1 releases -> Lock 2 can now acquire
    lock1.release()
    assert lock2.acquire() is True
    lock2.release()
    assert not os.path.exists(lock_file)
