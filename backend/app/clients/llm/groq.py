"""
GitNova v4.2 — Groq Free-Tier LLM Provider

Implements BaseLLMProvider using Groq's high-speed free tier API
with llama-3.3-70b-versatile for structured JSON generation.
"""

import json
import os
import requests
from typing import Type
from pydantic import BaseModel

from app.clients.llm.base import BaseLLMProvider
from app.core.config import settings


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider implementation for low-latency structured output."""

    def __init__(self, api_key: str = None, model: str = None):
        self._api_key = api_key or getattr(settings, "groq_api_key", "") or os.getenv("GROQ_API_KEY", "")
        cfg_model = getattr(settings, "llm_model", "llama-3.3-70b-versatile")
        if not cfg_model or "gemini" in cfg_model.lower() or "poolside" in cfg_model.lower():
            cfg_model = "llama-3.3-70b-versatile"
        self._model = model or os.getenv("GROQ_MODEL", cfg_model)
        self._base_url = "https://api.groq.com/openai/v1/chat/completions"

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._model

    def generate_structured(self, prompt: str, schema: Type[BaseModel]) -> BaseModel:
        """
        Calls Groq Chat Completions API with JSON mode constraint
        and parses output into the target Pydantic schema.
        """
        if not self._api_key:
            raise ValueError("GROQ_API_KEY is missing or empty.")

        json_schema_hint = schema.model_json_schema()
        system_instruction = (
            "You are the Lead Technical Mentor for GitNova v4.\n"
            "Respond strictly in valid JSON matching this JSON schema:\n"
            f"{json.dumps(json_schema_hint)}\n"
            "Do not include markdown code block backticks around your JSON response."
        )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 2048,
        }

        resp = None
        for attempt in range(3):
            try:
                resp = requests.post(self._base_url, headers=headers, json=payload, timeout=45)
                if resp.status_code == 429:
                    import time
                    print(f"⚠️ Groq rate limit hit (429), backing off {10 * (attempt + 1)}s...")
                    time.sleep(10 * (attempt + 1))
                    payload["model"] = "llama-3.1-8b-instant"
                    continue
                if resp.status_code != 200:
                    error_body = resp.text.replace(self._api_key, "[REDACTED]") if self._api_key else resp.text
                    raise RuntimeError(f"Groq API error (HTTP {resp.status_code}): {error_body}")
                break
            except RuntimeError:
                raise
            except Exception as e:
                if attempt == 2:
                    err_msg = str(e).replace(self._api_key, "[REDACTED]") if self._api_key else str(e)
                    raise RuntimeError(f"Groq API connection error: {err_msg}") from None
                import time
                time.sleep(5)

        if not resp or resp.status_code != 200:
            error_body = resp.text.replace(self._api_key, "[REDACTED]") if (resp and self._api_key) else "No response"
            raise RuntimeError(f"Groq API failed after retries: {error_body}")

        data = resp.json()
        content_str = data["choices"][0]["message"]["content"]
        
        # Clean any accidental wrapping markdown backticks
        clean_json_str = content_str.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:]
        if clean_json_str.startswith("```"):
            clean_json_str = clean_json_str[3:]
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-3]
        clean_json_str = clean_json_str.strip()

        parsed_dict = json.loads(clean_json_str)
        return schema.model_validate(parsed_dict)
