"""
Storage Service — S3 upload/download via boto3.
"""

import boto3

from app.core.config import settings

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", region_name=settings.aws_region)
    return _s3_client


async def upload_file(
    file_bytes: bytes, s3_key: str, content_type: str = "application/octet-stream"
) -> str:
    """Uploads bytes to S3 and returns the S3 URI."""
    get_s3_client().put_object(
        Bucket=settings.s3_bucket_name,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"s3://{settings.s3_bucket_name}/{s3_key}"


async def download_file(s3_key: str) -> bytes:
    """Downloads a file from S3 and returns its bytes."""
    response = get_s3_client().get_object(Bucket=settings.s3_bucket_name, Key=s3_key)
    return response["Body"].read()


async def list_files(prefix: str) -> list[str]:
    """Lists all object keys under a given S3 prefix."""
    paginator = get_s3_client().get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=settings.s3_bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys
