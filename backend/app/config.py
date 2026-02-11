from __future__ import annotations

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Nao Translation Bridge API"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "sqlite:///./nao_medical.db"

    ai_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_translation_model: str = "gemini-2.0-flash"
    gemini_summary_model: str = "gemini-2.0-flash"
    gemini_transcribe_model: str = "gemini-2.0-flash"
    ai_timeout_seconds: int = 20

    s3_endpoint_url: str = ""
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_public_base_url: str = ""

    max_audio_mb: int = 15
    allowed_audio_mime: str = "audio/webm"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def allowed_audio_mime_list(self) -> List[str]:
        return [item.strip() for item in self.allowed_audio_mime.split(",") if item.strip()]


settings = Settings()

if settings.ai_provider != "gemini":
    raise RuntimeError("Only AI_PROVIDER=gemini is implemented for this MVP")

if settings.app_env != "test":
    os.environ.setdefault("TZ", "UTC")
