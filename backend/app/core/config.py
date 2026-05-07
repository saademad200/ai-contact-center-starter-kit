"""
Application Settings (pydantic-settings)
==========================================
Loads from env vars / .env file. All settings documented with defaults.
"""

import json
import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


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

    @model_validator(mode="after")
    def load_aws_secrets(self) -> "Settings":
        """Load secrets from AWS Secrets Manager in staging/production."""
        if self.environment in ["staging", "prod"]:
            secret_name = f"alfalah-ai-{self.environment}/api"
            try:
                client = boto3.client("secretsmanager", region_name=self.aws_region)
                response = client.get_secret_value(SecretId=secret_name)
                secrets = json.loads(response["SecretString"])
                
                # Update attributes if they exist in the secret
                if "OPENAI_API_KEY" in secrets:
                    self.openai_api_key = secrets["OPENAI_API_KEY"]
                if "LANGFUSE_PUBLIC_KEY" in secrets:
                    self.langfuse_public_key = secrets["LANGFUSE_PUBLIC_KEY"]
                if "LANGFUSE_SECRET_KEY" in secrets:
                    self.langfuse_secret_key = secrets["LANGFUSE_SECRET_KEY"]
                if "JWT_SECRET_KEY" in secrets:
                    self.jwt_secret_key = secrets["JWT_SECRET_KEY"]
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Failed to load secrets from AWS Secrets Manager: {e}")
        
        return self


settings = Settings()
