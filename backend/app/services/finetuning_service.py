"""
Fine-Tuning Service
Uploads a cleaned JSONL file from S3 to OpenAI and triggers a fine-tuning job.
Registers the resulting model in the DynamoDB Model Registry.
"""

import os
import tempfile
from datetime import UTC, datetime
from typing import Any, cast

import boto3
from openai import AsyncOpenAI

_client = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "alfalah-ai-data-staging")
BASE_MODEL = "gpt-4o-mini-2024-07-18"  # cheapest fine-tuneable model


def _s3_client() -> Any:
    return boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))


async def upload_training_files(s3_keys: list[str]) -> str:
    """
    Downloads one or more JSONL files from S3, merges them into a single
    temporary file, uploads to OpenAI, and returns the OpenAI file_id.
    """
    s3 = _s3_client()
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="wb") as merged:
        for key in s3_keys:
            print(f"[FineTuning] Downloading s3://{S3_BUCKET}/{key}")
            s3.download_fileobj(S3_BUCKET, key, merged)
            merged.write(b"\n")  # ensure newline separation between files
        merged_path = merged.name

    with open(merged_path, "rb") as f:
        response = await _get_client().files.create(file=f, purpose="fine-tune")

    return cast(str, response.id)


async def trigger_fine_tuning_job(
    s3_keys: list[str],
) -> dict[str, Any]:
    """
    1. Downloads and merges JSONL files from S3.
    2. Uploads merged file to OpenAI.
    3. Creates a fine-tuning job.
    4. Returns job details for storage in DynamoDB Model Registry.
    """
    print(f"[FineTuning] Merging {len(s3_keys)} file(s) from s3://{S3_BUCKET}/")
    file_id = await upload_training_files(s3_keys)
    print(f"[FineTuning] OpenAI file uploaded: {file_id}")

    job = await _get_client().fine_tuning.jobs.create(
        training_file=file_id,
        model=BASE_MODEL,
        hyperparameters={"n_epochs": "auto"},
    )
    print(f"[FineTuning] Job created: {job.id} — status: {job.status}")

    return {
        "job_id": job.id,
        "file_id": file_id,
        "base_model": BASE_MODEL,
        "status": job.status,
        "created_at": datetime.now(UTC).isoformat(),
    }


async def check_fine_tuning_status(job_id: str) -> dict[str, Any]:
    """Returns the current status of a fine-tuning job."""
    job = await _get_client().fine_tuning.jobs.retrieve(job_id)
    return {
        "job_id": job.id,
        "status": job.status,
        "fine_tuned_model": job.fine_tuned_model,  # populated when job succeeds
        "finished_at": job.finished_at,
        "trained_tokens": job.trained_tokens,
    }


# ── Public aliases expected by llmops router ──────────────────────────────────


async def start_fine_tuning_job(s3_keys: list[str], suffix: str = "") -> str:
    """Starts a fine-tuning job from multiple S3 JSONL keys and returns the job_id."""
    result = await trigger_fine_tuning_job(s3_keys=s3_keys)
    return cast(str, result["job_id"])


async def get_job_status(job_id: str) -> dict[str, Any]:
    """Alias for check_fine_tuning_status."""
    return await check_fine_tuning_status(job_id)
