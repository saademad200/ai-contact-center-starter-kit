"""
Documents Router (admin KB management)
========================================
POST /api/v1/documents/upload
  - destination=rag       → chunks & embeds PDF into ChromaDB
  - destination=finetune  → uploads raw file to S3 raw/ prefix → Lambda processes it

GET  /api/v1/documents              — list uploaded documents
DELETE /api/v1/documents/{doc_id}   — remove from ChromaDB or mark deleted in DynamoDB
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.dependencies import require_admin
from app.core.dynamo import get_table
from app.services.storage_service import upload_file
from app.pipeline.ingestion import ingest_pdf

router = APIRouter(prefix="/documents", tags=["documents"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/upload")
async def upload_document(
    _: Annotated[dict, Depends(require_admin)],
    file: UploadFile = File(...),
    destination: Literal["rag", "finetune"] = Form("rag"),
    fund_name: str = Form(""),
):
    """
    Upload a document. Routes to RAG (ChromaDB) or Fine-Tuning (S3) based on destination.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_bytes = await file.read()
    doc_id = uuid.uuid4().hex
    created_at = _now_iso()

    record = {
        "pk": doc_id,
        "sk": "DOC",
        "filename": file.filename,
        "destination": destination,
        "fund_name": fund_name,
        "created_at": created_at,
        "status": "processing",
    }

    if destination == "rag":
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="RAG destination requires a PDF file")

        # Run ingestion pipeline: PDF → chunks → embeddings → ChromaDB
        chunks_count = await ingest_pdf(
            pdf_bytes=file_bytes,
            source_name=file.filename,
            fund_name=fund_name or file.filename,
        )
        record["status"] = "ingested"
        record["chunks_count"] = chunks_count

    else:  # finetune
        s3_key = f"raw/{doc_id}/{file.filename}"
        s3_uri = await upload_file(file_bytes, s3_key, file.content_type or "application/octet-stream")
        record["status"] = "uploaded_to_s3"
        record["s3_uri"] = s3_uri

    get_table("documents").put_item(Item=record)
    return {"doc_id": doc_id, "status": record["status"], "destination": destination}


@router.get("")
async def list_documents(_: Annotated[dict, Depends(require_admin)]):
    result = get_table("documents").scan()
    return {"documents": result.get("Items", [])}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, _: Annotated[dict, Depends(require_admin)]):
    table = get_table("documents")
    item = table.get_item(Key={"pk": doc_id, "sk": "DOC"}).get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")

    table.update_item(
        Key={"pk": doc_id, "sk": "DOC"},
        UpdateExpression="SET #s = :deleted",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":deleted": "deleted"},
    )
    return {"message": "Document marked as deleted"}
