from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime
from enum import Enum

# Enums dla walidacji
class FlashcardStatusEnum(str, Enum):
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"

class FlashcardSourceEnum(str, Enum):
    MANUAL = "manual"
    AI_SUGGESTION = "ai_suggestion"

class FlashcardManualCreateRequest(BaseModel):
    """Request model for creating a manual flashcard."""
    front_content: str = Field(
        ..., 
        description="Front content of the flashcard.", 
        min_length=1, 
        max_length=500
    )
    back_content: str = Field(
        ..., 
        description="Back content of the flashcard.", 
        min_length=1, 
        max_length=1000
    )

class FlashcardPatchRequest(BaseModel):
    """Request model for updating a flashcard (PATCH operation)."""
    front_content: Optional[str] = Field(
        None, 
        description="Optional new front content of the flashcard.", 
        min_length=1, 
        max_length=500
    )
    back_content: Optional[str] = Field(
        None, 
        description="Optional new back content of the flashcard.", 
        min_length=1, 
        max_length=1000
    )
    status: Optional[FlashcardStatusEnum] = Field(
        None, 
        description="Optional new status (for AI suggestions: 'active' or 'rejected')"
    )

class FlashcardResponse(BaseModel):
    """Response model for flashcard data."""
    id: uuid.UUID
    user_id: uuid.UUID
    source_text_id: Optional[uuid.UUID]
    front_content: str
    back_content: str
    source: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2

class ListFlashcardsQueryParams(BaseModel):
    """Query parameters for listing flashcards."""
    status: Optional[FlashcardStatusEnum] = Field(
        default=FlashcardStatusEnum.ACTIVE, 
        description="Filter by flashcard status"
    )
    source: Optional[FlashcardSourceEnum] = Field(
        default=None, 
        description="Filter by flashcard source"
    )
    page: int = Field(
        default=1, 
        ge=1, 
        description="Page number for pagination"
    )
    size: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Number of items per page"
    )

class PaginatedFlashcardsResponse(BaseModel):
    """Response model for paginated flashcards list."""
    items: List[FlashcardResponse]
    total: int = Field(description="Total number of flashcards matching criteria")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")
    pages: int = Field(description="Total number of pages") 