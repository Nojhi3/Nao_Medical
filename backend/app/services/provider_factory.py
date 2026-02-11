from __future__ import annotations

from .gemini import GeminiProvider
from .groq import GroqProvider
from ..config import settings


def get_ai_provider():
    provider = settings.ai_provider.strip().lower()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "groq":
        return GroqProvider()
    raise RuntimeError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")

