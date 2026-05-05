"""
WebSocket Chat Endpoint
========================
WS /ws/chat/{conversation_id}

Flow:
  1. Accept WebSocket connection.
  2. Load conversation history from DynamoDB.
  3. On each incoming message:
     a. Save user message to DynamoDB.
     b. Call agent orchestrator.
     c. Save assistant reply to DynamoDB.
     d. Send reply back over WebSocket.
"""

import contextlib
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.orchestrator import chat_with_agent
from app.core.dynamo import get_table

router = APIRouter(tags=["chat"])


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _save_message(conversation_id: str, role: str, content: str) -> dict[str, Any]:
    table = get_table("messages")
    msg: dict[str, Any] = {
        "pk": conversation_id,
        "sk": f"{_now_iso()}#{uuid.uuid4().hex[:8]}",
        "role": role,
        "content": content,
        "created_at": _now_iso(),
    }
    table.put_item(Item=msg)
    return msg


def _load_history(conversation_id: str) -> list[dict[str, Any]]:
    table = get_table("messages")
    response = table.query(
        KeyConditionExpression="pk = :pk",
        ExpressionAttributeValues={":pk": conversation_id},
        ScanIndexForward=True,
    )
    return [
        {"role": item["role"], "content": item["content"]}
        for item in response.get("Items", [])
    ]


def _ensure_conversation(conversation_id: str) -> None:
    table = get_table("conversations")
    table.put_item(
        Item={
            "pk": conversation_id,
            "sk": "META",
            "created_at": _now_iso(),
            "status": "active",
        },
        ConditionExpression="attribute_not_exists(pk)",
    )


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str) -> None:
    await websocket.accept()

    with contextlib.suppress(Exception):
        _ensure_conversation(conversation_id)

    try:
        while True:
            user_message = await websocket.receive_text()

            if not user_message.strip():
                continue

            history = _load_history(conversation_id)
            _save_message(conversation_id, "user", user_message)

            try:
                reply = await chat_with_agent(
                    conversation_history=history,
                    user_message=user_message,
                    conversation_id=conversation_id,
                )
            except Exception as e:
                reply = "I'm sorry, I encountered an error. Please try again."
                print(f"[WS] Agent error: {e}")

            _save_message(conversation_id, "assistant", reply)

            await websocket.send_text(reply)

    except WebSocketDisconnect:
        print(f"[WS] Disconnected: {conversation_id}")
