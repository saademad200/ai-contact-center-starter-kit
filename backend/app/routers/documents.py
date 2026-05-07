"""
Documents Router (admin KB management)
========================================
POST /api/v1/documents/upload        — accepts file, returns 202, ingests in background
GET  /api/v1/documents               — list uploaded documents
GET  /api/v1/documents/{doc_id}      — get single document status
DELETE /api/v1/documents/{doc_id}    — mark deleted
"""

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.core.dependencies import require_admin
from app.core.dynamo import get_table
from app.pipeline.ingestion import ingest_pdf
from app.services.storage_service import upload_file

router = APIRouter(prefix="/documents", tags=["documents"])


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _update_status(doc_id: str, status: str, extra: dict[str, Any] | None = None) -> None:
    expr = "SET #s = :s, updated_at = :u"
    vals: dict[str, Any] = {":s": status, ":u": _now_iso()}
    names = {"#s": "status"}
    if extra:
        for k, v in extra.items():
            expr += f", {k} = :{k}"
            vals[f":{k}"] = v
    get_table("documents").update_item(
        Key={"pk": doc_id, "sk": "DOC"},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=vals,
    )


async def _run_rag_ingestion(doc_id: str, file_bytes: bytes, filename: str, fund_name: str) -> None:
    try:
        chunks_count = await ingest_pdf(
            pdf_bytes=file_bytes,
            source_name=filename,
            fund_name=fund_name or filename,
        )
        _update_status(doc_id, "ingested", {"chunks_count": chunks_count})
    except Exception as exc:
        print(f"[Ingest] Failed for {doc_id}: {exc}")
        _update_status(doc_id, "failed", {"error": str(exc)})


@router.post("/upload", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    _: Annotated[dict, Depends(require_admin)],
    file: Annotated[UploadFile, File()],
    destination: Literal["rag", "finetune"] = Form("rag"),
    fund_name: str = Form(""),
) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    if destination == "rag" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="RAG destination requires a PDF file")

    file_bytes = await file.read()
    doc_id = uuid.uuid4().hex

    record: dict[str, Any] = {
        "pk": doc_id,
        "sk": "DOC",
        "filename": file.filename,
        "destination": destination,
        "fund_name": fund_name,
        "created_at": _now_iso(),
        "status": "processing",
    }

    if destination == "finetune":
        s3_key = f"raw/{doc_id}/{file.filename}"
        s3_uri = await upload_file(file_bytes, s3_key, file.content_type or "application/octet-stream")
        record["status"] = "uploaded_to_s3"
        record["s3_key"] = s3_key
        record["s3_uri"] = s3_uri
        get_table("documents").put_item(Item=record)
    else:
        get_table("documents").put_item(Item=record)
        background_tasks.add_task(_run_rag_ingestion, doc_id, file_bytes, file.filename, fund_name)

    return {"doc_id": doc_id, "status": record["status"], "destination": destination}


@router.get("")
async def list_documents(_: Annotated[dict, Depends(require_admin)]) -> dict[str, Any]:
    result = get_table("documents").scan()
    return {"documents": result.get("Items", [])}


@router.get("/{doc_id}")
async def get_document(doc_id: str, _: Annotated[dict, Depends(require_admin)]) -> dict[str, Any]:
    item = get_table("documents").get_item(Key={"pk": doc_id, "sk": "DOC"}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    return item


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, _: Annotated[dict, Depends(require_admin)]) -> dict[str, str]:
    table = get_table("documents")
    if not table.get_item(Key={"pk": doc_id, "sk": "DOC"}).get("Item"):
        raise HTTPException(status_code=404, detail="Document not found")
    _update_status(doc_id, "deleted")
    return {"message": "Document marked as deleted"}
