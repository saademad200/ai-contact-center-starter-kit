"""
LLMOps Router (admin)
======================
Prompt Registry CRUD and Fine-Tuning Job management.

GET    /api/v1/llmops/prompts            — list all prompt versions
POST   /api/v1/llmops/prompts            — create a new prompt version
PUT    /api/v1/llmops/prompts/{pk}/activate — set as ACTIVE_PROMPT

GET    /api/v1/llmops/models             — list fine-tuning jobs / model registry
POST   /api/v1/llmops/finetune           — trigger an OpenAI fine-tuning job

GET    /api/v1/llmops/finetune/{job_id}  — check job status
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import require_admin
from app.core.dynamo import get_table
from app.services.finetuning_service import get_job_status, start_fine_tuning_job

router = APIRouter(prefix="/llmops", tags=["llmops"])


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ── Prompt Registry ────────────────────────────────────────────────────────────


class PromptCreate(BaseModel):
    label: str
    content: str


@router.get("/prompts")
async def list_prompts(_: Annotated[dict, Depends(require_admin)]) -> dict[str, Any]:
    result = get_table("prompt-registry").scan()
    return {"prompts": result.get("Items", [])}


@router.post("/prompts", status_code=201)
async def create_prompt(
    body: PromptCreate,
    _: Annotated[dict, Depends(require_admin)],
) -> dict[str, Any]:
    pk = f"PROMPT#{uuid.uuid4().hex[:8]}"
    item: dict[str, Any] = {
        "pk": pk,
        "sk": "PROMPT",
        "label": body.label,
        "content": body.content,
        "created_at": _now_iso(),
        "is_active": False,
    }
    get_table("prompt-registry").put_item(Item=item)
    return item


@router.put("/prompts/{pk}/activate")
async def activate_prompt(
    pk: str, _: Annotated[dict, Depends(require_admin)]
) -> dict[str, str]:
    table = get_table("prompt-registry")

    resp = table.get_item(Key={"pk": pk, "sk": "PROMPT"})
    prompt = resp.get("Item")
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    table.put_item(
        Item={
            "pk": "ACTIVE_PROMPT",
            "sk": "ACTIVE_PROMPT",
            "content": prompt["content"],
            "source_pk": pk,
            "updated_at": _now_iso(),
        }
    )
    return {"message": f"Prompt {pk} is now active"}


# ── Model Registry / Fine-Tuning ───────────────────────────────────────────────


class FinetuneRequest(BaseModel):
    s3_key: str  # Path to cleaned JSONL in S3, e.g. "cleaned/my_data.jsonl"
    suffix: str = ""  # Optional suffix for the model name


@router.get("/models")
async def list_models(_: Annotated[dict, Depends(require_admin)]) -> dict[str, Any]:
    result = get_table("model-registry").scan()
    return {"models": result.get("Items", [])}


@router.post("/finetune", status_code=202)
async def trigger_finetune(
    body: FinetuneRequest,
    _: Annotated[dict, Depends(require_admin)],
) -> dict[str, str]:
    """Downloads JSONL from S3, uploads to OpenAI, and starts a fine-tuning job."""
    job_id = await start_fine_tuning_job(s3_key=body.s3_key, suffix=body.suffix)

    item: dict[str, Any] = {
        "pk": job_id,
        "sk": "FT_JOB",
        "s3_key": body.s3_key,
        "status": "pending",
        "created_at": _now_iso(),
    }
    get_table("model-registry").put_item(Item=item)
    return {"job_id": job_id, "status": "pending"}


@router.get("/finetune/{job_id}")
async def check_finetune_status(
    job_id: str, _: Annotated[dict, Depends(require_admin)]
) -> dict[str, Any]:
    """Checks the real-time status of a fine-tuning job from OpenAI."""
    job_status = await get_job_status(job_id)

    if job_status.get("status") in ("succeeded", "failed"):
        update_expr = "SET #s = :s, updated_at = :u"
        vals: dict[str, Any] = {":s": job_status["status"], ":u": _now_iso()}

        if job_status.get("fine_tuned_model"):
            update_expr += ", openai_model_id = :m, is_active = :a"
            vals[":m"] = job_status["fine_tuned_model"]
            vals[":a"] = False

        get_table("model-registry").update_item(
            Key={"pk": job_id, "sk": "FT_JOB"},
            UpdateExpression=update_expr,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues=vals,
        )

    return job_status


@router.put("/models/{job_id}/activate")
async def activate_model(
    job_id: str, _: Annotated[dict, Depends(require_admin)]
) -> dict[str, str]:
    """Sets a fine-tuned model as the active model in the registry."""
    table = get_table("model-registry")
    resp = table.get_item(Key={"pk": job_id, "sk": "FT_JOB"})
    model = resp.get("Item")
    if not model or not model.get("openai_model_id"):
        raise HTTPException(status_code=404, detail="Model not found or not ready")

    table.put_item(
        Item={
            "pk": "ACTIVE_MODEL",
            "sk": "ACTIVE_MODEL",
            "openai_model_id": model["openai_model_id"],
            "source_job_id": job_id,
            "updated_at": _now_iso(),
        }
    )
    return {"message": f"Model {model['openai_model_id']} is now active"}
