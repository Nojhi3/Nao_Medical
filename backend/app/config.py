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


settings = Settings()
