"""
GitNova LLM Provider — Google Gemini Implementation

Implements BaseLLMProvider using Google Gemini API (v1beta REST).
Primary Model: gemini-3.5-flash
Fallback Model: gemini-3.5-flash-lite
Features:
- Native structured JSON output enforcement (responseMimeType: "application/json")
- Dynamic RPM / TPM pacing and daily quota tracking (GeminiQuotaTracker)
- Bounded retries with exponential backoff, jitter, and Retry-After header support
- Thought-token resilient JSON extraction
"""

import json
import os
import re
import time
import random
import threading
import requests
from datetime import datetime, timezone
from typing import Type, Optional, Dict, Any
from pydantic import BaseModel, ValidationError

from app.clients.llm.base import BaseLLMProvider
from app.core.config import settings


class GeminiQuotaTracker:
    """
    Thread-safe request scheduler and quota tracker for Google Gemini API.
    Maintains rate-limiting pacing (RPM/TPM) and daily consumption metrics.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GeminiQuotaTracker, cls).__new__(cls)
                cls._instance._init_tracker()
            return cls._instance

    def _init_tracker(self):
        self.rpm_limit = getattr(settings, "gemini_rpm_limit", 13) or 13
        self.input_tpm_limit = getattr(settings, "gemini_input_tpm_limit", 1000000) or 1000000
        self.rpd_limit = getattr(settings, "gemini_rpd_limit", 1500) or 1500
        self.min_interval = 4.6  # Minimum 4.6s spacing guarantees max ~13 requests/minute with zero bursts

        self._last_request_time = 0.0
        self._minute_window_start = time.time()
        self._requests_this_minute = 0
        self._tokens_this_minute = 0

        self._day_date = datetime.now(timezone.utc).date()
        self._requests_today = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._rate_limit_hits = 0

    def acquire(self, estimated_tokens: int = 1500) -> None:
        """
        Paces incoming requests with inter-request spacing to prevent HTTP 429 bursts.
        """
        with self._lock:
            now = time.time()
            today = datetime.now(timezone.utc).date()

            # Reset daily counters if day rolled over
            if today != self._day_date:
                self._day_date = today
                self._requests_today = 0
                self._total_input_tokens = 0
                self._total_output_tokens = 0

            # Check daily quota limit
            if self._requests_today >= self.rpd_limit:
                raise RuntimeError(
                    f"Gemini daily quota limit reached ({self._requests_today}/{self.rpd_limit} RPD). "
                    "Stopping batch gracefully."
                )

            # Enforce smooth inter-request spacing (at least 4.6s between consecutive calls)
            time_since_last = now - self._last_request_time
            if time_since_last < self.min_interval:
                sleep_needed = self.min_interval - time_since_last
                time.sleep(sleep_needed)
                now = time.time()

            # Slide 1-minute window
            elapsed = now - self._minute_window_start
            if elapsed >= 60.0:
                self._minute_window_start = now
                self._requests_this_minute = 0
                self._tokens_this_minute = 0
            else:
                # If RPM limit or TPM limit would be exceeded, wait until minute window resets
                if (self._requests_this_minute >= self.rpm_limit) or (self._tokens_this_minute + estimated_tokens > self.input_tpm_limit):
                    wait_sec = max(1.0, 60.0 - elapsed + random.uniform(0.1, 0.5))
                    print(f"⏳ [GeminiScheduler] Pacing rate limit ({self._requests_this_minute}/{self.rpm_limit} RPM). Sleeping {wait_sec:.1f}s...")
                    time.sleep(wait_sec)
                    now = time.time()
                    self._minute_window_start = now
                    self._requests_this_minute = 0
                    self._tokens_this_minute = 0

            self._last_request_time = now
            self._requests_this_minute += 1
            self._tokens_this_minute += estimated_tokens
            self._requests_today += 1

    def record_usage(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Records token usage from completed response."""
        with self._lock:
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens

    def record_429(self) -> None:
        """Increments 429 rate limit hit counter."""
        with self._lock:
            self._rate_limit_hits += 1

    def is_daily_quota_exhausted(self) -> bool:
        with self._lock:
            return self._requests_today >= self.rpd_limit

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "rpm_limit": self.rpm_limit,
                "input_tpm_limit": self.input_tpm_limit,
                "rpd_limit": self.rpd_limit,
                "requests_this_minute": self._requests_this_minute,
                "tokens_this_minute": self._tokens_this_minute,
                "requests_today": self._requests_today,
                "remaining_daily_capacity": max(0, self.rpd_limit - self._requests_today),
                "rate_limit_429_hits": self._rate_limit_hits
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API LLM provider implementation with quota-controlled scheduling."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = (
            api_key
            or getattr(settings, "gemini_api_key", "")
            or os.getenv("GEMINI_API_KEY", "")
            or os.getenv("GOOGLE_API_KEY", "")
        )
        self._model = (
            model
            or getattr(settings, "gemini_model", "gemini-3.5-flash")
            or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        )
        self._base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self._scheduler = GeminiQuotaTracker()

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def generate_structured(self, prompt: str, schema: Type[BaseModel]) -> BaseModel:
        """
        Calls Gemini API with structured JSON output and parses into target Pydantic schema.
        Enforces rate-limit pacing and bounded exponential retries with Retry-After support.
        """
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY / GOOGLE_API_KEY is missing or empty in environment.")

        url = f"{self._base_url}/{self._model}:generateContent?key={self._api_key}"
        json_schema_hint = schema.model_json_schema()

        system_instruction = (
            "You are the Lead Open-Source Technical Mentor for GitNova.\n"
            "Analyze the verified issue evidence and codebase context.\n"
            "You MUST respond ONLY with a valid JSON object matching this schema:\n"
            f"{json.dumps(json_schema_hint)}\n"
            "Do NOT include markdown formatting, backticks, or preamble outside the JSON."
        )

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_instruction}\n\nTask Context & Input:\n{prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1,
                "maxOutputTokens": 8192
            }
        }

        estimated_prompt_tokens = max(100, int(len(prompt.split()) * 1.3))
        max_attempts = 3
        base_delay = 2.0

        for attempt in range(1, max_attempts + 1):
            # Enforce rate limit pacing before each network attempt
            self._scheduler.acquire(estimated_tokens=estimated_prompt_tokens)
            t0 = time.time()

            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=60)
                latency = round(time.time() - t0, 2)

                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise ValueError(f"Gemini returned empty candidates. Raw response: {data}")

                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    if not content_parts:
                        raise ValueError(f"Gemini candidate has no parts. Raw response: {data}")

                    raw_text = content_parts[0].get("text", "").strip()

                    # Clean markdown wrappers if present
                    if raw_text.startswith("```"):
                        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                        raw_text = re.sub(r"\s*```$", "", raw_text)
                    raw_text = raw_text.strip()

                    # Resiliently isolate JSON boundaries
                    start_idx = raw_text.find("{")
                    end_idx = raw_text.rfind("}")
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        raw_text = raw_text[start_idx:end_idx + 1]

                    # Parse and validate JSON
                    parsed_dict = json.loads(raw_text)
                    validated = schema.model_validate(parsed_dict)

                    # Record usage metadata
                    usage = data.get("usageMetadata", {})
                    in_toks = usage.get("promptTokenCount", estimated_prompt_tokens)
                    out_toks = usage.get("candidatesTokenCount", len(raw_text.split()))
                    self._scheduler.record_usage(input_tokens=in_toks, output_tokens=out_toks)

                    return validated

                elif resp.status_code == 429:
                    self._scheduler.record_429()
                    retry_after_hdr = resp.headers.get("Retry-After")
                    if retry_after_hdr and retry_after_hdr.isdigit():
                        sleep_time = float(retry_after_hdr) + random.uniform(0.5, 1.5)
                    else:
                        jitter = random.uniform(0.5, 1.5)
                        sleep_time = (base_delay * (2 ** (attempt - 1))) + jitter

                    print(
                        f"⚠️ [LLM:Gemini] Rate limit (HTTP 429) on attempt {attempt}/{max_attempts}. "
                        f"Backing off {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    continue

                elif resp.status_code in {500, 502, 503, 504}:
                    jitter = random.uniform(0.5, 1.0)
                    sleep_time = (base_delay * attempt) + jitter
                    print(
                        f"⚠️ [LLM:Gemini] Server error (HTTP {resp.status_code}) on attempt {attempt}/{max_attempts}. "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    continue

                elif resp.status_code == 413:
                    print(f"❌ [LLM:Gemini] Payload too large (HTTP 413). Bailing out.")
                    raise RuntimeError(f"Gemini API payload too large (HTTP 413): {resp.text[:300]}")

                else:
                    raise RuntimeError(f"Gemini API error (HTTP {resp.status_code}): {resp.text[:300]}")

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                jitter = random.uniform(0.5, 1.0)
                sleep_time = (base_delay * attempt) + jitter
                print(f"⚠️ [LLM:Gemini] Network error ({e.__class__.__name__}) on attempt {attempt}/{max_attempts}. Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                continue

        # If all attempts exhausted on primary model, attempt one fallback to gemini-3.5-flash-lite
        if self._model != "gemini-3.5-flash-lite":
            print(f"🔄 [LLM:Gemini] Primary model '{self._model}' exhausted retries. Trying fallback 'gemini-3.5-flash-lite'...")
            fallback_provider = GeminiProvider(api_key=self._api_key, model="gemini-3.5-flash-lite")
            return fallback_provider.generate_structured(prompt, schema)

        raise RuntimeError(f"Gemini API exhausted all {max_attempts} attempts on model '{self._model}'.")
