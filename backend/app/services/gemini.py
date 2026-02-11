from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from ..config import settings


class GeminiProvider:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required")
        self._base = "https://generativelanguage.googleapis.com/v1beta/models"

    async def _generate(self, model: str, parts: list[dict[str, Any]]) -> str:
        url = f"{self._base}/{model}:generateContent?key={settings.gemini_api_key}"
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.2},
        }
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            try:
                resp = await client.post(url, json=payload)
            except httpx.RequestError as exc:
                raise RuntimeError("gemini_request_failed") from exc
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    raise RuntimeError("gemini_rate_limited") from exc
                raise RuntimeError(f"gemini_http_{exc.response.status_code}") from exc
            data = resp.json()

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")
        parts_out = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts_out if isinstance(part, dict))
        if not text:
            raise RuntimeError("Gemini returned empty text")
        return text.strip()

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        prompt = (
            "Translate the following medical conversation text. "
            "Preserve meaning and medical terminology. "
            "Output only the translated text.\n\n"
            f"Source language: {source_lang}\n"
            f"Target language: {target_lang}\n"
            f"Text: {text}"
        )
        return await self._generate(settings.gemini_translation_model, [{"text": prompt}])

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str, language_hint: str) -> str:
        prompt = (
            "Transcribe this audio accurately for medical conversation context. "
            "Return plain text only with no extra commentary. "
            f"Language hint: {language_hint}."
        )
        encoded = base64.b64encode(audio_bytes).decode("utf-8")
        return await self._generate(
            settings.gemini_transcribe_model,
            [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": encoded}},
            ],
        )

    async def summarize_medical(self, lines: list[str], style: str) -> dict[str, Any]:
        prompt = (
            "You are summarizing a doctor-patient conversation. "
            "Return strict JSON with keys: summary (string), symptoms (array), diagnoses (array), medications (array), follow_up (array). "
            "No markdown. No extra keys.\n\n"
            f"Style: {style}\n"
            "Conversation:\n"
            + "\n".join(lines)
        )
        raw = await self._generate(settings.gemini_summary_model, [{"text": prompt}])
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("summary_parse_failed") from exc
        return {
            "summary": str(parsed.get("summary", "")).strip(),
            "symptoms": list(parsed.get("symptoms", []) or []),
            "diagnoses": list(parsed.get("diagnoses", []) or []),
            "medications": list(parsed.get("medications", []) or []),
            "follow_up": list(parsed.get("follow_up", []) or []),
        }
