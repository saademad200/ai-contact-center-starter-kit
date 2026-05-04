"""
Ratings Router — POST /api/v1/ratings
Allows widget to submit thumbs-up/thumbs-down on an assistant message.
"""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.dynamo import get_table

router = APIRouter(prefix="/ratings", tags=["ratings"])


class RatingCreate(BaseModel):
    conversation_id: str
    message_sk: str  # The sort-key of the message being rated
    rating: int  # 1 = thumbs up, -1 = thumbs down
    feedback: str = ""  # Optional free-text feedback


@router.post("", status_code=201)
async def submit_rating(body: RatingCreate):
    item = {
        "pk": f"RATING#{body.conversation_id}",
        "sk": f"{body.message_sk}",
        "rating": body.rating,
        "feedback": body.feedback,
        "created_at": datetime.now(UTC).isoformat(),
    }
    get_table("response-ratings").put_item(Item=item)
    return {"message": "Rating submitted"}
