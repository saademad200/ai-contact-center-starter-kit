"""Auth Router — POST /api/v1/auth/token (admin login)"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.dynamo import get_table
from app.core.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/token", response_model=Token)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Validates admin credentials and returns a JWT."""
    table = get_table("users")
    response = table.get_item(Key={"pk": form_data.username, "sk": "USER"})
    user = response.get("Item")

    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user["pk"], "role": user.get("role", "admin")})
    return Token(access_token=token, token_type="bearer")  # nosec B106
