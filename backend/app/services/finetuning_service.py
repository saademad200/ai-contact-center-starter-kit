"""
Fine-Tuning Service
Uploads a cleaned JSONL file from S3 to OpenAI and triggers a fine-tuning job.
Registers the resulting model in the DynamoDB Model Registry.
"""
import os
import boto3
import tempfile
from datetime import datetime, timezone
from typing import Optional

from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "alfalah-ai-data-staging")
BASE_MODEL = "gpt-4o-mini-2024-07-18"   # cheapest fine-tuneable model


def _s3_client():
    return boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-east-1"))


async def upload_training_file(s3_key: str) -> str:
    """
    Downloads the cleaned JSONL from S3, uploads it to OpenAI,
    and returns the OpenAI file_id.
    """
    s3 = _s3_client()
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
        s3.download_fileobj(S3_BUCKET, s3_key, tmp)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        response = await client.files.create(file=f, purpose="fine-tune")

    return response.id


async def trigger_fine_tuning_job(s3_key: str = "cleaned/training.jsonl") -> dict:
    """
    1. Downloads cleaned JSONL from S3.
    2. Uploads it to OpenAI.
    3. Creates a fine-tuning job.
    4. Returns job details for storage in DynamoDB Model Registry.
    """
    print(f"[FineTuning] Uploading training file from s3://{S3_BUCKET}/{s3_key}")
    file_id = await upload_training_file(s3_key)
    print(f"[FineTuning] OpenAI file uploaded: {file_id}")

    job = await client.fine_tuning.jobs.create(
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
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


async def check_fine_tuning_status(job_id: str) -> dict:
    """Returns the current status of a fine-tuning job."""
    job = await client.fine_tuning.jobs.retrieve(job_id)
    return {
        "job_id": job.id,
        "status": job.status,
        "fine_tuned_model": job.fine_tuned_model,  # populated when job succeeds
        "finished_at": job.finished_at,
        "trained_tokens": job.trained_tokens,
    }
