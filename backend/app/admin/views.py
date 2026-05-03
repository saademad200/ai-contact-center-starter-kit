"""
Admin Panel Views
==================
FastAPI routes that render Jinja2 templates.
Session-based auth (cookie) — separate from the REST API JWT.
Mounts at /admin via main.py.
"""
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.core.dynamo import get_table
from app.core.security import verify_password, create_access_token
from app.services.storage_service import upload_file
from app.pipeline.ingestion import ingest_pdf

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _get_session_user(request: Request) -> dict | None:
    return request.session.get("user")


def _require_login(request: Request) -> dict:
    user = _get_session_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/admin/login"},
        )
    return user


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ── Login / Logout ─────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _get_session_user(request):
        return RedirectResponse("/admin/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    table = get_table("users")
    resp = table.get_item(Key={"pk": username, "sk": "USER"})
    user = resp.get("Item")
    if not user or not verify_password(password, user.get("hashed_password", "")):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid credentials"}, status_code=401
        )
    request.session["user"] = {"username": user["pk"], "role": user.get("role", "admin")}
    return RedirectResponse("/admin/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=302)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, _=Depends(_require_login)):
    convs      = get_table("conversations").scan().get("Items", [])
    tickets    = get_table("tickets").scan().get("Items", [])
    docs       = get_table("documents").scan().get("Items", [])
    model_item = get_table("model-registry").get_item(Key={"pk": "ACTIVE_MODEL", "sk": "ACTIVE_MODEL"}).get("Item")
    prompt_item= get_table("prompt-registry").get_item(Key={"pk": "ACTIVE_PROMPT", "sk": "ACTIVE_PROMPT"}).get("Item")

    stats = {
        "total_conversations": len(convs),
        "open_tickets": sum(1 for t in tickets if t.get("status") == "open"),
        "total_documents": len(docs),
        "active_model": (model_item or {}).get("openai_model_id", "gpt-4o-mini"),
        "active_prompt": (prompt_item or {}).get("content", "No active prompt set."),
    }
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": stats, "active": "dashboard"})


# ── Conversations ─────────────────────────────────────────────────────────────

@router.get("/conversations", response_class=HTMLResponse)
async def conversations(request: Request, _=Depends(_require_login)):
    items = get_table("conversations").scan().get("Items", [])
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return templates.TemplateResponse("conversations.html", {"request": request, "conversations": items, "active": "conversations"})


@router.get("/conversations/{conv_id}", response_class=HTMLResponse)
async def conversation_detail(conv_id: str, request: Request, _=Depends(_require_login)):
    from boto3.dynamodb.conditions import Key
    conv = get_table("conversations").get_item(Key={"pk": conv_id, "sk": "META"}).get("Item")
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = get_table("messages").query(
        KeyConditionExpression=Key("pk").eq(conv_id), ScanIndexForward=True
    ).get("Items", [])
    return templates.TemplateResponse(
        "conversation_detail.html",
        {"request": request, "conversation": conv, "messages": messages, "active": "conversations"},
    )


@router.post("/conversations/{conv_id}/archive")
async def archive_conversation(conv_id: str, request: Request, _=Depends(_require_login)):
    get_table("conversations").update_item(
        Key={"pk": conv_id, "sk": "META"},
        UpdateExpression="SET #s = :v",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":v": "archived"},
    )
    return RedirectResponse("/admin/conversations", status_code=302)


# ── Tickets ───────────────────────────────────────────────────────────────────

@router.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request, _=Depends(_require_login)):
    items = get_table("tickets").scan().get("Items", [])
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return templates.TemplateResponse("tickets.html", {"request": request, "tickets": items, "active": "tickets"})


@router.post("/tickets/{ticket_id}/status")
async def update_ticket(ticket_id: str, request: Request, status: str = Form(...), _=Depends(_require_login)):
    get_table("tickets").update_item(
        Key={"pk": ticket_id, "sk": "TICKET"},
        UpdateExpression="SET #s = :v",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":v": status},
    )
    return RedirectResponse("/admin/tickets", status_code=302)


# ── Knowledge Base ────────────────────────────────────────────────────────────

@router.get("/knowledge-base", response_class=HTMLResponse)
async def knowledge_base(request: Request, _=Depends(_require_login)):
    docs = get_table("documents").scan().get("Items", [])
    docs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return templates.TemplateResponse("knowledge_base.html", {"request": request, "documents": docs, "active": "knowledge_base"})


@router.post("/knowledge-base/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    destination: str = Form("rag"),
    fund_name: str = Form(""),
    _=Depends(_require_login),
):
    import uuid
    file_bytes = await file.read()
    doc_id = uuid.uuid4().hex
    record = {
        "pk": doc_id, "sk": "DOC",
        "filename": file.filename, "destination": destination,
        "fund_name": fund_name, "created_at": _now_iso(), "status": "processing",
    }
    if destination == "rag":
        chunks = await ingest_pdf(pdf_bytes=file_bytes, source_name=file.filename or "doc", fund_name=fund_name or "general")
        record.update({"status": "ingested", "chunks_count": chunks})
    else:
        s3_key = f"raw/{doc_id}/{file.filename}"
        s3_uri = await upload_file(file_bytes, s3_key)
        record.update({"status": "uploaded_to_s3", "s3_uri": s3_uri})
    get_table("documents").put_item(Item=record)
    return RedirectResponse("/admin/knowledge-base", status_code=302)


@router.post("/knowledge-base/{doc_id}/delete")
async def delete_document(doc_id: str, request: Request, _=Depends(_require_login)):
    get_table("documents").update_item(
        Key={"pk": doc_id, "sk": "DOC"},
        UpdateExpression="SET #s = :v",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":v": "deleted"},
    )
    return RedirectResponse("/admin/knowledge-base", status_code=302)


# ── LLMOps ───────────────────────────────────────────────────────────────────

@router.get("/llmops", response_class=HTMLResponse)
async def llmops_page(request: Request, _=Depends(_require_login)):
    prompts = get_table("prompt-registry").scan().get("Items", [])
    jobs    = get_table("model-registry").scan().get("Items", [])
    jobs    = [j for j in jobs if j.get("sk") == "FT_JOB"]
    return templates.TemplateResponse("llmops.html", {"request": request, "prompts": prompts, "jobs": jobs, "active": "llmops"})


@router.post("/llmops/prompts")
async def create_prompt(request: Request, label: str = Form(...), content: str = Form(...), _=Depends(_require_login)):
    import uuid
    get_table("prompt-registry").put_item(Item={
        "pk": f"PROMPT#{uuid.uuid4().hex[:8]}", "sk": "PROMPT",
        "label": label, "content": content,
        "created_at": _now_iso(), "is_active": False,
    })
    return RedirectResponse("/admin/llmops", status_code=302)


@router.post("/llmops/prompts/{pk}/activate")
async def activate_prompt(pk: str, request: Request, _=Depends(_require_login)):
    table = get_table("prompt-registry")
    prompt = table.get_item(Key={"pk": pk, "sk": "PROMPT"}).get("Item")
    if not prompt:
        raise HTTPException(status_code=404)
    table.put_item(Item={"pk": "ACTIVE_PROMPT", "sk": "ACTIVE_PROMPT",
                         "content": prompt["content"], "source_pk": pk, "updated_at": _now_iso()})
    return RedirectResponse("/admin/llmops", status_code=302)


@router.post("/llmops/finetune")
async def trigger_finetune(request: Request, s3_key: str = Form(...), _=Depends(_require_login)):
    from app.services.finetuning_service import start_fine_tuning_job
    job_id = await start_fine_tuning_job(s3_key=s3_key)
    get_table("model-registry").put_item(Item={
        "pk": job_id, "sk": "FT_JOB", "s3_key": s3_key,
        "status": "pending", "created_at": _now_iso(),
    })
    return RedirectResponse("/admin/llmops", status_code=302)


@router.post("/llmops/models/{job_id}/activate")
async def activate_model(job_id: str, request: Request, _=Depends(_require_login)):
    table = get_table("model-registry")
    job = table.get_item(Key={"pk": job_id, "sk": "FT_JOB"}).get("Item")
    if not job or not job.get("openai_model_id"):
        raise HTTPException(status_code=400, detail="Model not ready")
    table.put_item(Item={"pk": "ACTIVE_MODEL", "sk": "ACTIVE_MODEL",
                         "openai_model_id": job["openai_model_id"],
                         "source_job_id": job_id, "updated_at": _now_iso()})
    return RedirectResponse("/admin/llmops", status_code=302)


# ── Quality ───────────────────────────────────────────────────────────────────

@router.get("/quality", response_class=HTMLResponse)
async def quality_page(request: Request, _=Depends(_require_login)):
    ratings = get_table("response-ratings").scan().get("Items", [])
    positive = sum(1 for r in ratings if r.get("rating") == 1)
    negative = sum(1 for r in ratings if r.get("rating") == -1)
    total = positive + negative
    score = round(positive / total * 100) if total else 0
    return templates.TemplateResponse("quality.html", {
        "request": request,
        "ratings": sorted(ratings, key=lambda x: x.get("created_at", ""), reverse=True)[:50],
        "stats": {"positive": positive, "negative": negative, "score": score},
        "active": "quality",
    })
