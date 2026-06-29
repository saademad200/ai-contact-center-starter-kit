"""
Application Settings (pydantic-settings)
==========================================
Loads from env vars / .env file. All settings documented with defaults.
"""

import json
from typing import Literal

import boto3
from pydantic import model_validator
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
    langfuse_base_url: str = ""  # alias used in .env / Secrets Manager

    # JWT Auth (admin panel)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480  # 8 hours

    # CORS — origins allowed to connect to the WebSocket / REST API
    cors_origins: list[str] = ["*"]

    # Vector store backend — "chromadb" (default) or "pgvector"
    vector_store_type: Literal["chromadb", "pgvector"] = "chromadb"
    # PostgreSQL connection string used when vector_store_type == "pgvector"
    database_url: str = ""
    # Embedding dimension used by the pgvector table (must match embedding model output)
    pgvector_dimension: int = 384

    @model_validator(mode="after")
    def validate_vector_store_config(self) -> "Settings":
        """Cross-validate vector store settings at startup."""
        if self.vector_store_type == "pgvector":
            if not self.database_url:
                raise ValueError(
                    "VECTOR_STORE_TYPE=pgvector requires DATABASE_URL to be set"
                )
            # Cross-check dimension against the embedding model to prevent silent corruption
            from app.services.embedding_service import EMBEDDING_DIMENSION

            if self.pgvector_dimension != EMBEDDING_DIMENSION:
                raise ValueError(
                    f"PGVECTOR_DIMENSION ({self.pgvector_dimension}) does not match "
                    f"EMBEDDING_DIMENSION ({EMBEDDING_DIMENSION}) from the embedding model. "
                    f"These must be equal to prevent silent data corruption."
                )
        return self

    @model_validator(mode="after")
    def load_aws_secrets(self) -> "Settings":
        """Load secrets from AWS Secrets Manager in staging/production."""
        if self.environment in ["staging", "prod"]:
            secret_name = f"alfalah-ai-{self.environment}/api"
            try:
                client = boto3.client("secretsmanager", region_name=self.aws_region)
                response = client.get_secret_value(SecretId=secret_name)
                secrets = json.loads(response["SecretString"])

                # Update attributes if they exist in the secret, and inject into os.environ
                import os

                if "OPENAI_API_KEY" in secrets:
                    self.openai_api_key = secrets["OPENAI_API_KEY"]
                    os.environ["OPENAI_API_KEY"] = secrets["OPENAI_API_KEY"]
                if "LANGFUSE_PUBLIC_KEY" in secrets:
                    self.langfuse_public_key = secrets["LANGFUSE_PUBLIC_KEY"]
                    os.environ["LANGFUSE_PUBLIC_KEY"] = secrets["LANGFUSE_PUBLIC_KEY"]
                if "LANGFUSE_SECRET_KEY" in secrets:
                    self.langfuse_secret_key = secrets["LANGFUSE_SECRET_KEY"]
                    os.environ["LANGFUSE_SECRET_KEY"] = secrets["LANGFUSE_SECRET_KEY"]
                # Support LANGFUSE_BASE_URL (the key name used in .env and Secrets Manager)
                langfuse_url = secrets.get("LANGFUSE_BASE_URL") or secrets.get("LANGFUSE_HOST")
                if langfuse_url:
                    self.langfuse_host = langfuse_url
                    os.environ["LANGFUSE_BASE_URL"] = langfuse_url
                    os.environ["LANGFUSE_HOST"] = langfuse_url
                if "JWT_SECRET_KEY" in secrets:
                    self.jwt_secret_key = secrets["JWT_SECRET_KEY"]
                    os.environ["JWT_SECRET_KEY"] = secrets["JWT_SECRET_KEY"]

                # Disable ChromaDB telemetry
                os.environ["ANONYMIZED_TELEMETRY"] = "False"

            except Exception as e:
                import logging

                logging.getLogger(__name__).warning(f"Failed to load secrets from AWS Secrets Manager: {e}")

        return self


settings = Settings()
