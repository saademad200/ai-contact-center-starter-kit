"""
Conversations Router (admin)
=============================
GET  /api/v1/conversations          — list all conversations
GET  /api/v1/conversations/{id}     — get conversation + messages
DELETE /api/v1/conversations/{id}   — delete conversation
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from boto3.dynamodb.conditions import Key

from app.core.dependencies import require_admin
from app.core.dynamo import get_table

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(_: Annotated[dict, Depends(require_admin)]):
    """List all conversations (scan — admin only)."""
    table = get_table("conversations")
    result = table.scan()
    return {"conversations": result.get("Items", [])}


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    _: Annotated[dict, Depends(require_admin)],
):
    """Get a conversation's metadata plus all its messages."""
    conv_table = get_table("conversations")
    msg_table = get_table("messages")

    conv = conv_table.get_item(Key={"pk": conversation_id, "sk": "META"}).get("Item")
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = msg_table.query(
        KeyConditionExpression=Key("pk").eq(conversation_id),
        ScanIndexForward=True,
    ).get("Items", [])

    return {"conversation": conv, "messages": messages}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    _: Annotated[dict, Depends(require_admin)],
):
    """Soft-delete a conversation by marking it archived."""
    table = get_table("conversations")
    table.update_item(
        Key={"pk": conversation_id, "sk": "META"},
        UpdateExpression="SET #s = :archived",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":archived": "archived"},
    )
    return {"message": "Conversation archived"}
