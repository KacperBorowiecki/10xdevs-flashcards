import logging
import math
import uuid
from typing import Optional

from src.api.v1.schemas.ai_schemas import PaginatedAiGenerationStatsResponse
from src.db.schemas import AiGenerationEvent
from supabase import Client

logger = logging.getLogger(__name__)


class AiGenerationServiceError(Exception):
    """Custom exception for AI Generation Service errors."""

    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"AI Generation Service Error in {operation}: {details}")


class AiGenerationService:
    """Service for AI generation statistics and operations."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def get_user_generation_stats(
        self, user_id: uuid.UUID, page: int, size: int
    ) -> PaginatedAiGenerationStatsResponse:
        """
        Get paginated AI generation statistics for a user.

        Args:
            user_id: User UUID
            page: Page number (starts from 1)
            size: Items per page

        Returns:
            Paginated response with AI generation events

        Raises:
            AiGenerationServiceError: If database operation fails
        """
        try:
            # Calculate offset for pagination
            offset = (page - 1) * size

            # Count total records for the user
            count_response = (
                self.supabase.table("ai_generation_events")
                .select("*", count="exact")
                .eq("user_id", str(user_id))
                .execute()
            )

            total = count_response.count or 0

            # Fetch paginated records
            data_response = (
                self.supabase.table("ai_generation_events")
                .select("*")
                .eq("user_id", str(user_id))
                .order("created_at", desc=True)
                .range(offset, offset + size - 1)
                .execute()
            )

            # Convert to Pydantic models
            items = []
            for record in data_response.data:
                # Convert record to AiGenerationEvent
                event = AiGenerationEvent(
                    id=record["id"],
                    user_id=record["user_id"],
                    source_text_id=record["source_text_id"],
                    generated_cards_count=record["generated_cards_count"],
                    accepted_cards_count=record["accepted_cards_count"],
                    rejected_cards_count=record["rejected_cards_count"],
                    llm_model_used=record.get("llm_model_used"),
                    cost=record.get("cost"),
                    created_at=record["created_at"],
                    updated_at=record["updated_at"],
                )
                items.append(event)

            # Calculate total pages (ceiling division)
            pages = math.ceil(total / size) if total > 0 else 1

            logger.info(
                f"Retrieved {len(items)} AI generation events for user {user_id} (page {page}/{pages})"
            )

            return PaginatedAiGenerationStatsResponse(
                items=items, total=total, page=page, size=size, pages=pages
            )

        except Exception as e:
            logger.error(
                f"Error retrieving AI generation stats for user {user_id}: {str(e)}"
            )
            raise AiGenerationServiceError(
                operation="get_user_generation_stats",
                details=f"Database query failed: {str(e)}",
            )


def get_ai_generation_service(supabase: Client) -> AiGenerationService:
    """Dependency factory for AiGenerationService."""
    return AiGenerationService(supabase)
