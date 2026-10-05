"""Pydantic schemas for works API."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class WorkBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    category_id: int

class WorkCreate(WorkBase):
    pass

class WorkUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    category_id: int | None = None

class WorkResponse(WorkBase):
    id: int
    author_id: int
    cover_url: str | None = None
    is_hidden: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WorkListResponse(BaseModel):
    items: list[WorkResponse]
    page: int
    limit: int
    total: int
    pages: int
