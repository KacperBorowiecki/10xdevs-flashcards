from typing import List

from pydantic import BaseModel, Field

from src.db.schemas import AiGenerationEvent


class AiGenerationStatsQueryParams(BaseModel):
    """Query parameters for AI generation statistics endpoint."""

    page: int = Field(default=1, ge=1, description="Page number for pagination")
    size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


class PaginatedAiGenerationStatsResponse(BaseModel):
    """Paginated response for AI generation statistics."""

    items: List[AiGenerationEvent]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
