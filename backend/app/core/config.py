"""
Application Settings (pydantic-settings)
==========================================
Loads from env vars / .env file. All settings documented with defaults.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    environment: str = "development"
    log_level: str = "INFO"

    # AWS
    aws_region: str = "us-east-1"
    s3_bucket_name: str = "alfalah-ai-training-data"
    dynamodb_endpoint_url: str | None = None  # Set for local dev only

    # OpenAI
    openai_api_key: str = ""

    # Langfuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # JWT Auth (admin panel)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480  # 8 hours

    # CORS — origins allowed to connect to the WebSocket / REST API
    cors_origins: list[str] = ["*"]


settings = Settings()
