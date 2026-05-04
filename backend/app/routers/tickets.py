"""
Tickets Router (admin) — escalations / support tickets
GET  /api/v1/tickets      — list all escalation tickets
PUT  /api/v1/tickets/{id} — update ticket status (open, in_progress, resolved)
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.dependencies import require_admin
from app.core.dynamo import get_table

router = APIRouter(prefix="/tickets", tags=["tickets"])


class TicketStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]


@router.get("")
async def list_tickets(_: Annotated[dict, Depends(require_admin)]):
    result = get_table("tickets").scan()
    return {"tickets": result.get("Items", [])}


@router.put("/{ticket_id}")
async def update_ticket_status(
    ticket_id: str,
    body: TicketStatusUpdate,
    _: Annotated[dict, Depends(require_admin)],
):
    table = get_table("tickets")
    resp = table.get_item(Key={"pk": ticket_id, "sk": "TICKET"})
    if not resp.get("Item"):
        raise HTTPException(status_code=404, detail="Ticket not found")

    table.update_item(
        Key={"pk": ticket_id, "sk": "TICKET"},
        UpdateExpression="SET #s = :s",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":s": body.status},
    )
    return {"message": f"Ticket {ticket_id} status updated to {body.status}"}
