"""
CLI script to create an admin user directly in DynamoDB.
Creates the users table automatically if it does not exist.

Usage (run from repo root with AWS credentials configured):
    python backend/scripts/create_admin.py <username> <password>

Optional flags:
    --env      Environment prefix: prod (default), staging, test
    --region   AWS region (default: us-east-1)
    --endpoint Local DynamoDB endpoint, e.g. http://localhost:8000
"""

import argparse
import sys
from datetime import UTC, datetime

import boto3
from botocore.exceptions import ClientError
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _ensure_table(dynamodb_client: object, table_name: str) -> None:
    try:
        dynamodb_client.describe_table(TableName=table_name)
        return
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceNotFoundException":
            raise

    print(f"Table '{table_name}' not found — creating it...")
    dynamodb_client.create_table(
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
    waiter = dynamodb_client.get_waiter("table_exists")
    waiter.wait(TableName=table_name)
    print(f"Table '{table_name}' created.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an admin user in DynamoDB.")
    parser.add_argument("username", help="Admin username")
    parser.add_argument("password", help="Admin password (min 8 chars)")
    parser.add_argument("--env", default="prod", help="Environment prefix (prod, staging, test)")
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--endpoint", default=None, help="Local DynamoDB endpoint URL")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("Error: password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    boto_kwargs: dict = {"region_name": args.region}
    if args.endpoint:
        boto_kwargs["endpoint_url"] = args.endpoint

    table_name = f"alfalah-ai-{args.env}-users"
    print(f"Using table: {table_name}")

    client = boto3.client("dynamodb", **boto_kwargs)
    _ensure_table(client, table_name)

    dynamodb = boto3.resource("dynamodb", **boto_kwargs)
    table = dynamodb.Table(table_name)

    existing = table.get_item(Key={"pk": args.username, "sk": "USER"}).get("Item")
    if existing:
        print(f"Error: user '{args.username}' already exists.", file=sys.stderr)
        sys.exit(1)

    table.put_item(
        Item={
            "pk": args.username,
            "sk": "USER",
            "hashed_password": pwd_context.hash(args.password),
            "role": "admin",
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    print(f"Admin user '{args.username}' created successfully.")


if __name__ == "__main__":
    main()
