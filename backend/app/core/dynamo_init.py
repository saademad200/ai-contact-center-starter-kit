"""
DynamoDB Table Initializer (CLI script)
========================================
Usage: python -m app.core.dynamo_init

Creates all 8 tables for the current environment:
  alfalah-ai-{env}-conversations
  alfalah-ai-{env}-messages
  alfalah-ai-{env}-tickets
  alfalah-ai-{env}-documents
  alfalah-ai-{env}-users
  alfalah-ai-{env}-response-ratings
  alfalah-ai-{env}-prompt-registry
  alfalah-ai-{env}-model-registry

All tables use pk (HASH) + sk (RANGE), PAY_PER_REQUEST billing.
Safe to re-run — existing tables are skipped.
"""

import logging

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TABLE_SUFFIXES = [
    "conversations",
    "messages",
    "tickets",
    "documents",
    "users",
    "response-ratings",
    "prompt-registry",
    "model-registry",
]


def _get_client() -> object:
    return boto3.client(
        "dynamodb",
        region_name=settings.aws_region,
        endpoint_url=settings.dynamodb_endpoint_url,
    )


def _create_table(client: object, table_name: str) -> None:
    try:
        client.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        client.get_waiter("table_exists").wait(TableName=table_name)
        logger.info("Created:        %s", table_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            logger.info("Already exists: %s", table_name)
        else:
            raise


def main() -> None:
    client = _get_client()
    endpoint = settings.dynamodb_endpoint_url or "AWS"
    logger.info("Initializing DynamoDB tables (env=%s, endpoint=%s)", settings.environment, endpoint)

    for suffix in TABLE_SUFFIXES:
        table_name = f"alfalah-ai-{settings.environment}-{suffix}"
        _create_table(client, table_name)

    logger.info("Done — %d tables ready.", len(TABLE_SUFFIXES))


if __name__ == "__main__":
    main()
