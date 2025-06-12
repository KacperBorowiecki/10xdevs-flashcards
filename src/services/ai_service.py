import logging
import uuid
from datetime import datetime
from typing import List

from src.db.schemas import (
    AiGenerationEventCreate,
    FlashcardCreate,
    FlashcardSourceEnum,
    FlashcardStatusEnum,
    SourceTextCreate,
    UserFlashcardSpacedRepetitionCreate,
)
from src.dtos import (
    AIGenerateFlashcardsRequest,
    AIGenerateFlashcardsResponse,
    FlashcardResponse,
)
from src.services.llm_client import LLMClient, LLMServiceError
from supabase import Client

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Raised when AI service operations fail."""

    def __init__(self, operation: str, details: str, user_id: uuid.UUID = None):
        self.operation = operation
        self.details = details
        self.user_id = user_id
        super().__init__(f"AI service error during {operation}: {details}")


class AIService:
    """Service for AI-powered flashcard generation."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def generate_flashcards_from_text(
        self, request: AIGenerateFlashcardsRequest, user_id: uuid.UUID
    ) -> AIGenerateFlashcardsResponse:
        """
        Generate flashcards from text using AI and save to database.

        Args:
            request: Request containing text content
            user_id: ID of the authenticated user

        Returns:
            Response with generated flashcards and metadata

        Raises:
            AIServiceError: If any step of the process fails
        """
        operation = "generate_flashcards_from_text"
        logger.info(f"Starting AI flashcard generation for user {user_id}")

        try:
            # Step 1: Create source_text record
            source_text = await self._create_source_text(
                text_content=request.text_content, user_id=user_id
            )
            logger.info(f"Created source text {source_text['id']} for user {user_id}")

            # Step 2: Generate flashcards using LLM
            llm_response = await self._generate_with_llm(request.text_content)
            logger.info(
                f"LLM generated {len(llm_response.flashcards)} flashcards using {llm_response.model_used}"
            )

            # Step 3: Create flashcard records with active status
            created_flashcards = await self._create_flashcard_records(
                llm_suggestions=llm_response.flashcards,
                user_id=user_id,
                source_text_id=uuid.UUID(source_text["id"]),
            )
            logger.info(f"Created {len(created_flashcards)} flashcard records")

            # Step 3.5: Create spaced repetition records for all flashcards
            await self._create_spaced_repetition_records(
                flashcards=created_flashcards, user_id=user_id
            )
            logger.info(
                f"Created spaced repetition records for {len(created_flashcards)} flashcards"
            )

            # Step 4: Create AI generation event record
            ai_event = await self._create_ai_generation_event(
                user_id=user_id,
                source_text_id=uuid.UUID(source_text["id"]),
                generated_count=len(llm_response.flashcards),
                model_used=llm_response.model_used,
                cost=llm_response.cost,
            )
            logger.info(f"Created AI generation event {ai_event['id']}")

            # Step 5: Convert to response models
            flashcard_responses = [
                FlashcardResponse(**flashcard) for flashcard in created_flashcards
            ]

            response = AIGenerateFlashcardsResponse(
                source_text_id=uuid.UUID(source_text["id"]),
                ai_generation_event_id=uuid.UUID(ai_event["id"]),
                suggested_flashcards=flashcard_responses,
            )

            logger.info(
                f"Successfully completed AI flashcard generation for user {user_id}"
            )
            return response

        except LLMServiceError as e:
            logger.error(f"LLM service error for user {user_id}: {e.details}")
            raise AIServiceError(
                operation=operation,
                details=f"LLM service failed: {e.details}",
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"Unexpected error in AI service for user {user_id}: {str(e)}")
            raise AIServiceError(
                operation=operation,
                details=f"Unexpected error: {str(e)}",
                user_id=user_id,
            )

    async def _create_source_text(self, text_content: str, user_id: uuid.UUID) -> dict:
        """Create source text record in database."""
        try:
            source_text_data = SourceTextCreate(
                user_id=user_id, text_content=text_content
            )

            result = (
                self.supabase.table("source_texts")
                .insert(source_text_data.model_dump(mode="json"))
                .execute()
            )

            if not result.data:
                raise AIServiceError(
                    operation="create_source_text",
                    details="Failed to insert source text record",
                    user_id=user_id,
                )

            return result.data[0]

        except Exception as e:
            logger.error(
                f"Database error creating source text for user {user_id}: {str(e)}"
            )
            raise AIServiceError(
                operation="create_source_text",
                details=f"Database operation failed: {str(e)}",
                user_id=user_id,
            )

    async def _generate_with_llm(self, text_content: str):
        """Generate flashcards using LLM service."""
        async with LLMClient() as llm_client:
            return await llm_client.generate_flashcards(text_content)

    async def _create_flashcard_records(
        self, llm_suggestions: List, user_id: uuid.UUID, source_text_id: uuid.UUID
    ) -> List[dict]:
        """Create flashcard records in database from LLM suggestions."""
        try:
            flashcard_creates = []

            for suggestion in llm_suggestions:
                flashcard_data = FlashcardCreate(
                    user_id=user_id,
                    front_content=suggestion.front_content,
                    back_content=suggestion.back_content,
                    source=FlashcardSourceEnum.AI_SUGGESTION,
                    status=FlashcardStatusEnum.ACTIVE,
                    source_text_id=source_text_id,
                )
                flashcard_creates.append(flashcard_data.model_dump(mode="json"))

            if not flashcard_creates:
                raise AIServiceError(
                    operation="create_flashcards",
                    details="No flashcards to create",
                    user_id=user_id,
                )

            result = (
                self.supabase.table("flashcards").insert(flashcard_creates).execute()
            )

            if not result.data:
                raise AIServiceError(
                    operation="create_flashcards",
                    details="Failed to insert flashcard records",
                    user_id=user_id,
                )

            return result.data

        except Exception as e:
            logger.error(
                f"Database error creating flashcards for user {user_id}: {str(e)}"
            )
            raise AIServiceError(
                operation="create_flashcards",
                details=f"Database operation failed: {str(e)}",
                user_id=user_id,
            )

    async def _create_spaced_repetition_records(
        self, flashcards: List[dict], user_id: uuid.UUID
    ) -> List[dict]:
        """Create spaced repetition records for AI-generated flashcards."""
        try:
            spaced_repetition_creates = []

            for flashcard in flashcards:
                flashcard_id = flashcard["id"]
                spaced_repetition_data = UserFlashcardSpacedRepetitionCreate(
                    user_id=user_id,
                    flashcard_id=uuid.UUID(flashcard_id),
                    due_date=datetime.utcnow(),  # Ready for first review
                    current_interval=1,
                    last_reviewed_at=None,
                )
                spaced_repetition_creates.append(
                    spaced_repetition_data.model_dump(mode="json")
                )

            if not spaced_repetition_creates:
                raise AIServiceError(
                    operation="create_spaced_repetition",
                    details="No spaced repetition records to create",
                    user_id=user_id,
                )

            result = (
                self.supabase.table("user_flashcard_spaced_repetition")
                .insert(spaced_repetition_creates)
                .execute()
            )

            if not result.data:
                raise AIServiceError(
                    operation="create_spaced_repetition",
                    details="Failed to insert spaced repetition records",
                    user_id=user_id,
                )

            return result.data

        except Exception as e:
            logger.error(
                f"Database error creating spaced repetition records for user {user_id}: {str(e)}"
            )
            raise AIServiceError(
                operation="create_spaced_repetition",
                details=f"Database operation failed: {str(e)}",
                user_id=user_id,
            )

    async def _create_ai_generation_event(
        self,
        user_id: uuid.UUID,
        source_text_id: uuid.UUID,
        generated_count: int,
        model_used: str,
        cost: float = None,
    ) -> dict:
        """Create AI generation event record in database."""
        try:
            event_data = AiGenerationEventCreate(
                user_id=user_id,
                source_text_id=source_text_id,
                generated_cards_count=generated_count,
                accepted_cards_count=0,  # Initially 0, will be updated when user reviews
                rejected_cards_count=0,  # Initially 0, will be updated when user reviews
                llm_model_used=model_used,
                cost=cost,
            )

            result = (
                self.supabase.table("ai_generation_events")
                .insert(event_data.model_dump(exclude_none=True, mode="json"))
                .execute()
            )

            if not result.data:
                raise AIServiceError(
                    operation="create_ai_event",
                    details="Failed to insert AI generation event record",
                    user_id=user_id,
                )

            return result.data[0]

        except Exception as e:
            logger.error(
                f"Database error creating AI event for user {user_id}: {str(e)}"
            )
            raise AIServiceError(
                operation="create_ai_event",
                details=f"Database operation failed: {str(e)}",
                user_id=user_id,
            )


def get_ai_service(supabase_client: Client) -> AIService:
    """Dependency function to get AI service instance."""
    return AIService(supabase_client)
