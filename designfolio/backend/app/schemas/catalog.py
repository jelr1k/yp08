"""Schemas for catalog categories and tags."""
from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TagResponse(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)
