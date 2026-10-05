"""Pydantic schemas for work likes."""
from datetime import datetime
from pydantic import BaseModel

class LikeResponse(BaseModel):
    liked: bool
    likes_count: int
    created_at: datetime | None = None
