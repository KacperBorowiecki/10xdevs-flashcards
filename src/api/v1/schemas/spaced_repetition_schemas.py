import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.db.schemas import FlashcardBase


class SpacedRepetitionQueryParams(BaseModel):
    """Query parameters for spaced repetition endpoints."""

    limit: Optional[int] = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of cards to return (1-100, default: 20)",
    )


class RepetitionData(BaseModel):
    """Spaced repetition data for a flashcard."""

    due_date: datetime = Field(description="Date when the card is due for review")
    current_interval: int = Field(
        description="Current spaced repetition interval in days"
    )
    last_reviewed_at: Optional[datetime] = Field(
        default=None, description="Timestamp of last review (null if never reviewed)"
    )

    class Config:
        from_attributes = True


class FlashcardWithRepetition(FlashcardBase):
    """Flashcard with associated spaced repetition data."""

    repetition_data: RepetitionData = Field(description="Spaced repetition information")

    class Config:
        from_attributes = True


class SpacedRepetitionReviewRequest(BaseModel):
    """Request DTO for submitting flashcard review result."""

    flashcard_id: uuid.UUID = Field(
        ..., description="ID of the flashcard being reviewed"
    )
    performance_rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Performance rating (1-5): 1=Again, 2=Hard, 3=Good, 4=Easy, 5=Perfect",
    )


class SpacedRepetitionReviewResponse(BaseModel):
    """Response DTO for flashcard review result."""

    id: uuid.UUID = Field(description="Spaced repetition record ID")
    user_id: uuid.UUID = Field(description="User ID")
    flashcard_id: uuid.UUID = Field(description="Flashcard ID")
    due_date: datetime = Field(description="Next due date for review")
    current_interval: int = Field(description="Current interval in days")
    last_reviewed_at: datetime = Field(description="Last review timestamp")
    data_extra: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional spaced repetition data"
    )
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Record last update timestamp")

    model_config = {"from_attributes": True}


class ReviewFlashcardCommand(BaseModel):
    """Command model for processing flashcard review."""

    user_id: uuid.UUID = Field(description="Authenticated user ID")
    flashcard_id: uuid.UUID = Field(description="Flashcard ID to review")
    performance_rating: int = Field(ge=1, le=5, description="Performance rating (1-5)")
