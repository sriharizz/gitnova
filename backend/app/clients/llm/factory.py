"""
GitNova LLM Provider Factory & Resilient Multi-Provider Orchestrator

Instantiates and orchestrates LLM providers based on configuration.
Supports seamless failover:
Primary: Gemini (gemini-3.6-flash)
Fallback 1: Gemini Lite (gemini-3.5-flash-lite)
Fallback 2: Groq (llama-3.3-70b-versatile)
"""

import os
from typing import Dict, Type, Optional
from pydantic import BaseModel

from app.clients.llm.base import BaseLLMProvider
from app.clients.llm.gemini import GeminiProvider
from app.clients.llm.groq import GroqProvider
from app.clients.llm.nvidia import NvidiaProvider
from app.core.config import settings


class ResilientLLMProvider(BaseLLMProvider):
    """
    Orchestrator that wraps multiple LLM providers and cascades on failure.
    Ensures zero downtime by routing requests to secondary providers if the primary fails.
    """

    def __init__(self, primary_provider: BaseLLMProvider):
        self._primary = primary_provider

    @property
    def provider_name(self) -> str:
        return self._primary.provider_name

    @property
    def model_name(self) -> str:
        return self._primary.model_name

    def generate_structured(self, prompt: str, schema: Type[BaseModel]) -> BaseModel:
        """
        Executes structured generation using primary provider, cascading to fallbacks on failure.
        """
        try:
            return self._primary.generate_structured(prompt, schema)
        except Exception as e:
            print(f"⚠️ [LLM:Orchestrator] Primary provider '{self._primary.provider_name}' failed: {e}")

            # Fallback 1: If primary is Gemini, try Gemini Lite (handled inside GeminiProvider) or Groq
            if self._primary.provider_name != "groq":
                groq_key = getattr(settings, "groq_api_key", "") or os.getenv("GROQ_API_KEY", "")
                if groq_key:
                    print(f"🔄 [LLM:Orchestrator] Cascading to secondary fallback provider 'groq' (llama-3.3-70b-versatile)...")
                    try:
                        groq_provider = GroqProvider()
                        return groq_provider.generate_structured(prompt, schema)
                    except Exception as ge:
                        print(f"❌ [LLM:Orchestrator] Secondary fallback 'groq' also failed: {ge}")

            raise e


class LLMProviderFactory:
    """Factory creating BaseLLMProvider instances based on configuration."""

    _registry: Dict[str, Type[BaseLLMProvider]] = {
        "gemini": GeminiProvider,
        "groq": GroqProvider,
        "nvidia": NvidiaProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: Optional[str] = None) -> BaseLLMProvider:
        """
        Returns the configured provider instance wrapped with resilient failover.
        
        Args:
            provider_name: Optional override. Defaults to settings.llm_provider or 'gemini'.
        """
        name = (
            provider_name
            or getattr(settings, "llm_provider", "gemini")
            or os.getenv("LLM_PROVIDER", "gemini")
        ).lower()

        provider_cls = cls._registry.get(name, GeminiProvider)
        primary = provider_cls()
        return ResilientLLMProvider(primary)
