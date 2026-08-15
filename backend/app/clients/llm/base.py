"""
GitNova v4.2 — Base LLM Provider Interface

Defines the abstract contract for pluggable LLM provider backends.
Enables zero-cost provider swapping (Groq, OpenRouter, Ollama, Gemini).
"""

from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel


class BaseLLMProvider(ABC):
    """Abstract interface for replaceable LLM backends."""

    @abstractmethod
    def generate_structured(self, prompt: str, schema: Type[BaseModel]) -> BaseModel:
        """
        Generates a structured Pydantic response from a grounded prompt.
        
        Args:
            prompt: The formatted system + context + user instruction prompt string.
            schema: The target Pydantic BaseModel class for validation.
            
        Returns:
            An instance of the schema populated with LLM generation outputs.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns provider identifier string (e.g. 'groq')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns model identifier string (e.g. 'llama-3.3-70b-versatile')."""
        pass
