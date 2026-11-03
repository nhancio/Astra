"""Google Gemini API wrapper for LLM calls (REST, so thinking level is set per call)."""

import asyncio
import json
import logging
import time
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.models.admin import ModelCall
from app.models.database import async_session
from app.services.runtime import get_runtime_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FALLBACK_RESPONSE = (
    "I am here for you, but I am having a moment. Try again in a bit?"
)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiService:
    """Wrapper around Google Gemini for text and JSON generation.

    Shared configuration selects JSON, simple and complex reply models.
    Flash-Lite uses minimal thinking; Flash uses low thinking.
    """

    MODEL_NAME = "gemini-3.8-flash"
    FAST_MODEL_NAME = "gemini-3.5-flash-lite"
    # Defaults remain available to integrations and routing regression tests.
    JSON_MODEL_NAME = "gemini-3.1-flash-lite"
    REQUEST_TIMEOUT_SECONDS = 20
    # Flash replies measured p95 ~6s; a stalled call gets cut here and retried once on Flash-Lite
    # inside the remaining REQUEST_TIMEOUT budget, instead of a 20s wait ending in FALLBACK_RESPONSE.
    FLASH_TIMEOUT_SECONDS = 10

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT_SECONDS)
        return self._client

    async def _generate(self, model: str, thinking: str, body: dict[str, Any]) -> str:
        body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": thinking}
        started = time.monotonic()
        status, usage = "error", {}
        try:
            client = self._get_client()
            resp = await client.post(API_URL.format(model=model), json=body,
                                     headers={"x-goog-api-key": settings.GEMINI_API_KEY})
            if resp.status_code != 200:
                raise RuntimeError(f"Gemini {model} HTTP {resp.status_code}")
            payload = resp.json()
            usage = payload.get("usageMetadata", {})
            parts = payload["candidates"][0]["content"].get("parts", [])
            text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            status = "success" if text else "empty"
            return text
        except asyncio.CancelledError:
            status = "timeout"
            raise
        finally:
            # Telemetry cannot turn an otherwise successful response into a failed reply.
            try:
                async with asyncio.timeout(0.5):
                    async with async_session() as db:
                        db.add(ModelCall(model=model, route="json" if body["generationConfig"].get("responseMimeType") else "reply",
                                         status=status, latency_ms=round((time.monotonic() - started) * 1000),
                                         input_tokens=usage.get("promptTokenCount"), output_tokens=usage.get("candidatesTokenCount")))
                        await db.commit()
            except Exception:
                logger.warning("Model telemetry write unavailable")

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[list[dict[str, str]]] = None,
        fast: bool = False,
        json_output: bool = False,
    ) -> str:
        """Call Gemini and return the generated text. `fast` = Flash-Lite; `json_output` forces JSON MIME."""
        try:
            contents = [
                {
                    "role": "model" if turn.get("role") == "assistant" else "user",
                    "parts": [{"text": turn.get("content", "")}],
                }
                for turn in history or []
            ]
            contents.append({"role": "user", "parts": [{"text": user_message}]})
            body = {
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "contents": contents,
                "generationConfig": {"temperature": 0.7, "topP": 0.95, "maxOutputTokens": 1024},
            }
            if json_output:
                body["generationConfig"]["responseMimeType"] = "application/json"
            config = await get_runtime_settings()
            model = config.json_model if fast and json_output else config.fast_model if fast else config.reply_model
            thinking = "minimal" if "lite" in model else "low"

            async with asyncio.timeout(self.REQUEST_TIMEOUT_SECONDS):
                if fast:
                    text = await self._generate(model, thinking, body)
                else:
                    try:
                        async with asyncio.timeout(self.FLASH_TIMEOUT_SECONDS):
                            text = await self._generate(model, thinking, body)
                    except Exception as exc:
                        logger.warning("Gemini %s failed (%r); retrying on %s", model, exc, config.fast_model)
                        text = await self._generate(config.fast_model, "minimal" if "lite" in config.fast_model else "low", body)
            return text or FALLBACK_RESPONSE

        except Exception as exc:
            logger.error("Gemini API error: %r", exc)
            return FALLBACK_RESPONSE

    async def generate_json_response(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[list[dict[str, str]]] = None,
    ) -> dict[str, Any]:
        """Call Gemini (fast model) expecting a JSON response. Parses and returns dict."""
        raw = await self.generate_response(
            system_prompt, user_message, history, fast=True, json_output=True
        )

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            first_newline = cleaned.index("\n") if "\n" in cleaned else 3
            cleaned = cleaned[first_newline + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini JSON response: %s", raw[:200])
            return {}
