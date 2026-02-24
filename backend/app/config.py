from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Nao Translation Bridge API"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "sqlite:///./nao_medical.db"

    ai_provider: str = "groq"
    gemini_api_key: str = ""
    gemini_translation_model: str = "gemini-2.0-flash"
    gemini_summary_model: str = "gemini-2.0-flash"
    gemini_transcribe_model: str = "gemini-2.0-flash"
    groq_api_key: str = ""
    groq_translation_model: str = "llama-3.1-8b-instant"
    groq_summary_model: str = "llama-3.3-70b-versatile"
    groq_transcribe_model: str = "whisper-large-v3-turbo"
    ai_timeout_seconds: int = 20

    s3_endpoint_url: str = ""
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_public_base_url: str = ""

    max_audio_mb: int = 15
    allowed_audio_mime: str = "audio/webm"

    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_ENV_PATH), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def allowed_audio_mime_list(self) -> List[str]:
        return [item.strip() for item in self.allowed_audio_mime.split(",") if item.strip()]

    def validate_required_settings(self) -> None:
        if self.ai_provider not in {"groq", "gemini"}:
            raise RuntimeError("AI_PROVIDER must be 'groq' or 'gemini'")

        strict_mode = self.app_env in {"staging", "production"}

        if self.app_env != "test":
            if not self.cors_origin_list:
                raise RuntimeError("CORS_ORIGINS must contain at least one origin")
            if not self.database_url:
                raise RuntimeError("DATABASE_URL is required")

        if strict_mode and self.ai_provider == "groq" and not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required when AI_PROVIDER=groq")

        if strict_mode and self.ai_provider == "gemini" and not self.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")

        s3_values = [
            self.s3_endpoint_url,
            self.s3_bucket,
            self.s3_region,
            self.s3_access_key_id,
            self.s3_secret_access_key,
            self.s3_public_base_url,
        ]
        if any(s3_values) and not all(s3_values):
            raise RuntimeError(
                "S3 config is incomplete. Set S3_ENDPOINT_URL, S3_BUCKET, S3_REGION, "
                "S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, and S3_PUBLIC_BASE_URL together."
            )


settings = Settings()

if settings.app_env != "test":
    os.environ.setdefault("TZ", "UTC")
