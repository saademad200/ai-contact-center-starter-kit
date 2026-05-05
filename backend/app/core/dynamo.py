"""
DynamoDB Client & Table Helpers
=================================
Provides get_dynamodb_resource() and get_table(suffix).

Table suffixes:
  conversations, messages, tickets, documents, users,
  response-ratings, prompt-registry, model-registry
"""

from functools import lru_cache
from typing import Any

import boto3

from app.core.config import settings


@lru_cache(maxsize=1)
def get_dynamodb_resource() -> Any:
    return boto3.resource(
        "dynamodb",
        region_name=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,  # None in prod
    )


def get_table(table_suffix: str) -> Any:
    """Returns a DynamoDB Table object using the alfalah-ai-{env}- prefix."""
    return get_dynamodb_resource().Table(f"alfalah-ai-{settings.environment}-{table_suffix}")
