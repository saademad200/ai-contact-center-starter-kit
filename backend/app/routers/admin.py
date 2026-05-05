from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from app.core.dependencies import require_admin
from app.core.dynamo import get_table
from app.core.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("username cannot be blank")
        return v

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class UserResponse(BaseModel):
    username: str
    role: str
    created_at: str | None = None


@router.get("/ratings")
async def list_ratings(_: Annotated[dict, Depends(require_admin)]) -> dict[str, Any]:
    items = get_table("response-ratings").scan().get("Items", [])
    return {"ratings": items}


@router.get("/stats")
async def get_dashboard_stats(_: Annotated[dict, Depends(require_admin)]) -> dict[str, Any]:
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


@router.get("/users", response_model=list[UserResponse])
async def list_users(_: Annotated[dict, Depends(require_admin)]) -> list[UserResponse]:
    items = (
        get_table("users").scan(FilterExpression="sk = :sk", ExpressionAttributeValues={":sk": "USER"}).get("Items", [])
    )
    return [UserResponse(username=u["pk"], role=u.get("role", "admin"), created_at=u.get("created_at")) for u in items]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    _: Annotated[dict, Depends(require_admin)],
) -> UserResponse:
    table = get_table("users")
    if table.get_item(Key={"pk": body.username, "sk": "USER"}).get("Item"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    now = datetime.now(UTC).isoformat()
    table.put_item(
        Item={
            "pk": body.username,
            "sk": "USER",
            "hashed_password": hash_password(body.password),
            "role": "admin",
            "created_at": now,
        }
    )
    return UserResponse(username=body.username, role="admin", created_at=now)


@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    username: str,
    current_user: Annotated[dict, Depends(require_admin)],
) -> None:
    if username == current_user.get("sub"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")

    table = get_table("users")
    if not table.get_item(Key={"pk": username, "sk": "USER"}).get("Item"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    table.delete_item(Key={"pk": username, "sk": "USER"})
