"""
GitNova v4.2 — NVIDIA LLM Provider Implementation

Implements BaseLLMProvider using NVIDIA's high-speed integrate API
with poolside/laguna-xs-2.1 for structured JSON generation.
Handles 429 rate limits and 503/502 worker capacity errors with backoff retries.
"""

import json
import os
import re
import time
import requests
from typing import Type
from pydantic import BaseModel

from app.clients.llm.base import BaseLLMProvider
from app.core.config import settings


class NvidiaProvider(BaseLLMProvider):
    """NVIDIA integrate API LLM provider implementation."""

    def __init__(self, api_key: str = None, model: str = None):
        self._api_key = api_key or getattr(settings, "nvidia_api_key", "") or os.getenv("NVIDIA_API_KEY", "")
        self._model = model or getattr(settings, "nvidia_model", "poolside/laguna-xs-2.1") or os.getenv("NVIDIA_MODEL", "poolside/laguna-xs-2.1")
        self._base_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    @property
    def provider_name(self) -> str:
        return "nvidia"

    @property
    def model_name(self) -> str:
        return self._model

    def generate_structured(self, prompt: str, schema: Type[BaseModel]) -> BaseModel:
        """
        Calls NVIDIA Chat Completions API with JSON output constraint
        and parses result into target Pydantic schema.
        """
        if not self._api_key:
            raise ValueError("NVIDIA_API_KEY is missing or empty in environment.")

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
            "Accept": "application/json"
        }

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        try:
            payload["response_format"] = {"type": "json_object"}
        except Exception:
            pass

        retry_count = 0
        max_retries = 8
        resp = None

        while retry_count <= max_retries:
            try:
                resp = requests.post(self._base_url, headers=headers, json=payload, timeout=120)
                if resp.status_code == 200:
                    break
                elif resp.status_code in (429, 502, 503, 504):
                    retry_count += 1
                    # Parse Retry-After header if available
                    retry_after = resp.headers.get("retry-after") or resp.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_sec = float(retry_after) + 2.0
                    else:
                        wait_sec = 6.0 * (1.5 ** (retry_count - 1))
                    wait_sec = min(wait_sec, 45.0)
                    print(f"\n[NVIDIA API {resp.status_code} Capacity/Rate Limit] Retrying in {wait_sec:.1f}s (Attempt {retry_count}/{max_retries})...", flush=True)
                    time.sleep(wait_sec)
                else:
                    err_text = resp.text.replace(self._api_key, "[REDACTED]")
                    raise RuntimeError(f"NVIDIA API error (HTTP {resp.status_code}): {err_text}")
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count > max_retries:
                    raise RuntimeError("NVIDIA API call timed out after 120s max retries.")
                time.sleep(6.0)
            except Exception as e:
                err_msg = str(e).replace(self._api_key, "[REDACTED]")
                if any(code in err_msg for code in ("429", "502", "503", "504", "rate", "resourceexhausted", "limit")):
                    retry_count += 1
                    wait_sec = min(8.0 * (1.5 ** (retry_count - 1)), 45.0)
                    print(f"\n[NVIDIA API Retryable Error] Sleeping {wait_sec:.1f}s (Attempt {retry_count}/{max_retries})...", flush=True)
                    time.sleep(wait_sec)
                else:
                    raise RuntimeError(f"NVIDIA API connection error: {err_msg}") from None

        if not resp or resp.status_code != 200:
            err_text = resp.text.replace(self._api_key, "[REDACTED]") if resp else "No response"
            raise RuntimeError(f"NVIDIA API request failed: {err_text}")

        data = resp.json()
        content_str = data["choices"][0]["message"]["content"]

        clean_json_str = content_str.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:]
        if clean_json_str.startswith("```"):
            clean_json_str = clean_json_str[3:]
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-3]
        clean_json_str = clean_json_str.strip()

        if not (clean_json_str.startswith("{") and clean_json_str.endswith("}")):
            start_idx = clean_json_str.find("{")
            end_idx = clean_json_str.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                clean_json_str = clean_json_str[start_idx:end_idx+1]

        parsed_dict = json.loads(clean_json_str)
        return schema.model_validate(parsed_dict)
