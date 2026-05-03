from fastapi import APIRouter, Depends
from app.core.dynamo import get_table
from app.core.security import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
async def get_dashboard_stats(_=Depends(require_admin)):
    convs = get_table("conversations").scan().get("Items", [])
    tickets = get_table("tickets").scan().get("Items", [])
    docs = get_table("documents").scan().get("Items", [])
    
    model_item = get_table("model-registry").get_item(Key={"pk": "ACTIVE_MODEL", "sk": "ACTIVE_MODEL"}).get("Item")
    prompt_item = get_table("prompt-registry").get_item(Key={"pk": "ACTIVE_PROMPT", "sk": "ACTIVE_PROMPT"}).get("Item")

    return {
        "total_conversations": len(convs),
        "open_tickets": sum(1 for t in tickets if t.get("status") == "open"),
        "total_documents": len(docs),
        "active_model": (model_item or {}).get("openai_model_id", "gpt-4o-mini"),
        "active_prompt": (prompt_item or {}).get("content", "No active prompt set."),
    }
