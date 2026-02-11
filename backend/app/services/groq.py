from __future__ import annotations

import json
from typing import Any

import httpx

from ..config import settings


class GroqProvider:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required")
        self._base = "https://api.groq.com/openai/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.groq_api_key}",
        }

    async def _chat(self, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        url = f"{self._base}/chat/completions"
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            try:
                resp = await client.post(url, headers=self._headers(), json=payload)
            except httpx.RequestError as exc:
                raise RuntimeError("groq_request_failed") from exc
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    raise RuntimeError("groq_rate_limited") from exc
                raise RuntimeError(f"groq_http_{exc.response.status_code}") from exc
            data = resp.json()

        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("groq_empty_response")
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("groq_empty_response")
        return content.strip()

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return await self._chat(
            model=settings.groq_translation_model,
            system_prompt="You are a medical translator. Preserve meaning and medical terminology.",
            user_prompt=(
                f"Translate from {source_lang} to {target_lang}. "
                "Return only translated text.\n\n"
                f"Text: {text}"
            ),
            temperature=0.0,
        )

    async def transcribe_audio(self, audio_bytes: bytes, mime_type: str, language_hint: str) -> str:
        url = f"{self._base}/audio/transcriptions"
        files = {
            "file": ("audio.webm", audio_bytes, mime_type),
        }
        data = {
            "model": settings.groq_transcribe_model,
            "language": language_hint,
            "response_format": "verbose_json",
        }
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            try:
                resp = await client.post(url, headers=self._headers(), data=data, files=files)
            except httpx.RequestError as exc:
                raise RuntimeError("groq_request_failed") from exc
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    raise RuntimeError("groq_rate_limited") from exc
                raise RuntimeError(f"groq_http_{exc.response.status_code}") from exc
            payload = resp.json()
        text = str(payload.get("text", "")).strip()
        if not text:
            raise RuntimeError("groq_empty_transcript")
        return text

    async def summarize_medical(self, lines: list[str], style: str) -> dict[str, Any]:
        raw = await self._chat(
            model=settings.groq_summary_model,
            system_prompt="You summarize clinical conversations and return strict JSON only.",
            user_prompt=(
                "Return strict JSON with keys: summary (string), symptoms (array), diagnoses (array), "
                "medications (array), follow_up (array). No markdown.\n\n"
                f"Style: {style}\n"
                "Conversation:\n"
                + "\n".join(lines)
            ),
            temperature=0.1,
        )
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

