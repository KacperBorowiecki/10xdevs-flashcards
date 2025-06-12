import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.api.v1.schemas.spaced_repetition_schemas import (
    FlashcardWithRepetition,
    RepetitionData,
    ReviewFlashcardCommand,
    SpacedRepetitionReviewResponse,
)
from src.db.schemas import FlashcardBase
from supabase import Client

logger = logging.getLogger(__name__)


class SpacedRepetitionService:
    """Service for managing spaced repetition operations."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def _validate_user_access(self, user_id: uuid.UUID) -> None:
        """
        Validate user access with additional security checks.

        Args:
            user_id: User UUID to validate

        Raises:
            ValueError: If user_id is invalid
        """
        if not user_id:
            raise ValueError("User ID is required")

        # Check for nil UUID (additional security)
        if user_id == uuid.UUID("00000000-0000-0000-0000-000000000000"):
            raise ValueError("Invalid user ID provided")

    def _calculate_next_interval(
        self, current_interval: int, performance_rating: int
    ) -> tuple[int, datetime]:
        """
        Calculate next interval using simplified SM-2 algorithm.

        Args:
            current_interval: Current interval in days
            performance_rating: Rating from 1-5 (1=Again, 2=Hard, 3=Good, 4=Easy, 5=Perfect)

        Returns:
            Tuple of (new_interval_days, due_date)
        """
        # SM-2 inspired algorithm with modifications for 1-5 scale
        if performance_rating <= 2:  # Again/Hard - reset or reduce interval
            if performance_rating == 1:  # Again
                new_interval = 1  # Reset to 1 day
            else:  # Hard (2)
                new_interval = max(1, int(current_interval * 0.6))  # Reduce by 40%
        else:  # Good/Easy/Perfect - increase interval
            if performance_rating == 3:  # Good
                multiplier = 1.3
            elif performance_rating == 4:  # Easy
                multiplier = 2.0
            else:  # Perfect (5)
                multiplier = 2.5

            new_interval = max(1, int(current_interval * multiplier))

        # Cap maximum interval at 365 days (1 year)
        new_interval = min(new_interval, 365)

        # Calculate due date
        due_date = datetime.utcnow() + timedelta(days=new_interval)

        return new_interval, due_date

    async def _validate_flashcard_access(
        self, user_id: uuid.UUID, flashcard_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Validate that flashcard exists, belongs to user, and is active.

        Args:
            user_id: User UUID
            flashcard_id: Flashcard UUID

        Returns:
            Flashcard data dictionary

        Raises:
            ValueError: If flashcard doesn't exist, doesn't belong to user, or isn't active
        """
        try:
            # Optimized query: select only necessary fields to reduce bandwidth
            response = (
                self.supabase.table("flashcards")
                .select("id, user_id, status, created_at")
                .eq("id", str(flashcard_id))
                .eq("user_id", str(user_id))
                .eq(
                    "status", "active"
                )  # Filter active status in query for better performance
                .single()  # Use single() for single record queries
                .execute()
            )

            if not response.data:
                raise ValueError(
                    "Flashcard not found, doesn't belong to user, or is not active"
                )

            flashcard = response.data

            # Additional security: Check if flashcard is too old (potential abuse)
            created_at = datetime.fromisoformat(
                flashcard["created_at"].replace("Z", "+00:00")
            )
            if created_at.tzinfo:
                created_at = created_at.replace(tzinfo=None)

            days_since_creation = (datetime.utcnow() - created_at).days
            if days_since_creation > 3650:  # 10 years - reasonable limit
                logger.warning(
                    f"Attempt to review very old flashcard | flashcard_id={flashcard_id} | days_old={days_since_creation}"
                )
                raise ValueError("Flashcard is too old for review")

            return flashcard

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            logger.error(f"Error validating flashcard access: {str(e)}")
            raise ValueError("Failed to validate flashcard access")

    async def _get_or_create_repetition_record(
        self, user_id: uuid.UUID, flashcard_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing spaced repetition record or return None if doesn't exist.
        Optimized for performance with minimal data transfer.

        Args:
            user_id: User UUID
            flashcard_id: Flashcard UUID

        Returns:
            Existing repetition record or None
        """
        try:
            # Optimized query: select only necessary fields
            response = (
                self.supabase.table("user_flashcard_spaced_repetition")
                .select("id, current_interval, data_extra, created_at")
                .eq("user_id", str(user_id))
                .eq("flashcard_id", str(flashcard_id))
                .single()  # Use single() for better performance
                .execute()
            )

            return response.data if response.data else None

        except Exception as e:
            # Log but don't raise - missing record is expected for new flashcards
            logger.debug(
                f"No existing repetition record found for flashcard {flashcard_id}"
            )
            return None

    def _validate_review_frequency(
        self, existing_record: Optional[Dict[str, Any]]
    ) -> None:
        """
        Validate that user isn't reviewing too frequently (rate limiting).

        Args:
            existing_record: Existing repetition record if any

        Raises:
            ValueError: If review frequency is too high
        """
        if not existing_record:
            return  # New flashcard, no frequency limit

        # Check if user is reviewing too frequently (potential abuse)
        data_extra = existing_record.get("data_extra", {})
        last_review_count = data_extra.get("review_count", 0)

        # Rate limiting: Maximum 50 reviews per flashcard per day
        if last_review_count > 50:
            created_at = datetime.fromisoformat(
                existing_record["created_at"].replace("Z", "+00:00")
            )
            if created_at.tzinfo:
                created_at = created_at.replace(tzinfo=None)

            hours_since_creation = (
                datetime.utcnow() - created_at
            ).total_seconds() / 3600
            if hours_since_creation < 24:  # Within 24 hours
                logger.warning(
                    f"Rate limit exceeded for flashcard review | reviews={last_review_count}"
                )
                raise ValueError(
                    "Too many reviews for this flashcard today. Please try again later."
                )

    def _sanitize_performance_rating(self, rating: int) -> int:
        """
        Additional sanitization of performance rating.

        Args:
            rating: Raw performance rating

        Returns:
            Sanitized rating

        Raises:
            ValueError: If rating is invalid
        """
        # Ensure rating is integer and within bounds
        if not isinstance(rating, int):
            raise ValueError("Performance rating must be an integer")

        # Clamp rating to valid range (defense in depth)
        rating = max(1, min(5, rating))

        return rating

    async def review_flashcard(
        self, command: ReviewFlashcardCommand
    ) -> SpacedRepetitionReviewResponse:
        """
        Process flashcard review and update spaced repetition data.
        Enhanced with performance optimizations and security checks.

        Args:
            command: Review command with user_id, flashcard_id, and performance_rating

        Returns:
            Updated spaced repetition data

        Raises:
            ValueError: If validation fails
            Exception: If database operations fail
        """
        try:
            # Enhanced security validation
            self._validate_user_access(command.user_id)

            # Sanitize performance rating (defense in depth)
            sanitized_rating = self._sanitize_performance_rating(
                command.performance_rating
            )

            logger.info(
                f"Processing flashcard review | user_id={command.user_id} | "
                f"flashcard_id={command.flashcard_id} | rating={sanitized_rating}"
            )

            # Validate flashcard access (optimized query)
            flashcard_data = await self._validate_flashcard_access(
                command.user_id, command.flashcard_id
            )

            # Get existing repetition record (optimized query)
            existing_record = await self._get_or_create_repetition_record(
                command.user_id, command.flashcard_id
            )

            # Rate limiting validation
            self._validate_review_frequency(existing_record)

            # Calculate new interval and due date
            current_interval = (
                existing_record.get("current_interval", 1) if existing_record else 1
            )
            new_interval, due_date = self._calculate_next_interval(
                current_interval, sanitized_rating
            )

            # Prepare optimized upsert data
            now = datetime.utcnow()
            review_count = (
                (existing_record.get("data_extra", {}).get("review_count", 0) + 1)
                if existing_record
                else 1
            )

            upsert_data = {
                "user_id": str(command.user_id),
                "flashcard_id": str(command.flashcard_id),
                "due_date": due_date.isoformat() + "Z",  # Ensure UTC timezone
                "current_interval": new_interval,
                "last_reviewed_at": now.isoformat() + "Z",
                "data_extra": {
                    "last_performance_rating": sanitized_rating,
                    "review_count": review_count,
                    "algorithm_version": "sm2_v1",  # Track algorithm version
                },
                "updated_at": now.isoformat() + "Z",
            }

            # Add ID and created_at for new records
            if not existing_record:
                upsert_data.update(
                    {"id": str(uuid.uuid4()), "created_at": now.isoformat() + "Z"}
                )

            # Optimized upsert with conflict resolution
            response = (
                self.supabase.table("user_flashcard_spaced_repetition")
                .upsert(
                    upsert_data, on_conflict="user_id,flashcard_id"
                )  # Specify conflict columns
                .execute()
            )

            if not response.data:
                raise Exception("Failed to upsert spaced repetition record")

            updated_record = response.data[0]

            # Create response with proper timezone handling
            result = SpacedRepetitionReviewResponse(
                id=uuid.UUID(updated_record["id"]),
                user_id=uuid.UUID(updated_record["user_id"]),
                flashcard_id=uuid.UUID(updated_record["flashcard_id"]),
                due_date=datetime.fromisoformat(
                    updated_record["due_date"].replace("Z", "+00:00")
                ).replace(tzinfo=None),
                current_interval=updated_record["current_interval"],
                last_reviewed_at=datetime.fromisoformat(
                    updated_record["last_reviewed_at"].replace("Z", "+00:00")
                ).replace(tzinfo=None),
                data_extra=updated_record.get("data_extra"),
                created_at=datetime.fromisoformat(
                    updated_record["created_at"].replace("Z", "+00:00")
                ).replace(tzinfo=None),
                updated_at=datetime.fromisoformat(
                    updated_record["updated_at"].replace("Z", "+00:00")
                ).replace(tzinfo=None),
            )

            logger.info(
                f"Successfully processed flashcard review | user_id={command.user_id} | "
                f"flashcard_id={command.flashcard_id} | new_interval={new_interval} | "
                f"due_date={due_date.isoformat()} | review_count={review_count}"
            )

            return result

        except ValueError as e:
            logger.warning(f"Validation error in flashcard review: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing flashcard review: {str(e)}")
            raise

    async def get_due_flashcards(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> List[FlashcardWithRepetition]:
        """
        Get flashcards that are due for review with spaced repetition data.

        Args:
            user_id: UUID of the authenticated user
            limit: Maximum number of cards to return (1-100)

        Returns:
            List of FlashcardWithRepetition objects

        Raises:
            ValueError: If input validation fails
            Exception: If database operations fail
        """
        try:
            # Enhanced security validation
            self._validate_user_access(user_id)

            if not (1 <= limit <= 100):
                raise ValueError("Limit must be between 1 and 100")

            logger.info(f"Getting due flashcards for user {user_id} with limit {limit}")

            # Query with JOIN to get flashcards with spaced repetition data
            # Using Supabase's query builder with foreign key relationships
            query = (
                self.supabase.table("flashcards")
                .select(
                    """
                    *,
                    user_flashcard_spaced_repetition:user_flashcard_spaced_repetition(
                        due_date,
                        current_interval,
                        last_reviewed_at
                    )
                """
                )
                .eq("user_id", str(user_id))
                .eq("status", "active")
            )

            # Execute query
            response = query.execute()

            if not response.data:
                logger.info(f"No flashcards found for user {user_id}")
                return []

            # Filter flashcards that are due and have spaced repetition data
            due_flashcards = []
            current_time = datetime.utcnow()

            for flashcard_data in response.data:
                # Check if flashcard has spaced repetition data
                sr_data = flashcard_data.get("user_flashcard_spaced_repetition")
                if not sr_data or not sr_data:
                    continue

                # Get the first (and should be only) spaced repetition record
                sr_record = (
                    sr_data[0] if isinstance(sr_data, list) and sr_data else sr_data
                )
                if not sr_record:
                    continue

                # Check if card is due
                due_date_str = sr_record.get("due_date")
                if not due_date_str:
                    continue

                # Parse due date
                try:
                    due_date = datetime.fromisoformat(
                        due_date_str.replace("Z", "+00:00")
                    )
                    if due_date.tzinfo:
                        due_date = due_date.replace(tzinfo=None)
                except (ValueError, AttributeError):
                    logger.warning(
                        f"Invalid due_date format for flashcard {flashcard_data.get('id')}"
                    )
                    continue

                # Only include cards that are due
                if due_date <= current_time:
                    # Parse last_reviewed_at if present
                    last_reviewed_at = None
                    if sr_record.get("last_reviewed_at"):
                        try:
                            last_reviewed_at = datetime.fromisoformat(
                                sr_record["last_reviewed_at"].replace("Z", "+00:00")
                            )
                            if last_reviewed_at.tzinfo:
                                last_reviewed_at = last_reviewed_at.replace(tzinfo=None)
                        except (ValueError, AttributeError):
                            logger.warning(
                                f"Invalid last_reviewed_at format for flashcard {flashcard_data.get('id')}"
                            )

                    # Create RepetitionData object
                    repetition_data = RepetitionData(
                        due_date=due_date,
                        current_interval=sr_record.get("current_interval", 1),
                        last_reviewed_at=last_reviewed_at,
                    )

                    # Remove the joined data from flashcard_data before creating FlashcardBase
                    clean_flashcard_data = {
                        k: v
                        for k, v in flashcard_data.items()
                        if k != "user_flashcard_spaced_repetition"
                    }

                    # Create FlashcardWithRepetition object
                    flashcard_with_repetition = FlashcardWithRepetition(
                        **clean_flashcard_data, repetition_data=repetition_data
                    )

                    due_flashcards.append(flashcard_with_repetition)

            # Sort by due_date (earliest first) and limit results
            due_flashcards.sort(key=lambda card: card.repetition_data.due_date)
            limited_cards = due_flashcards[:limit]

            logger.info(f"Found {len(limited_cards)} due flashcards for user {user_id}")
            return limited_cards

        except ValueError as e:
            logger.warning(
                f"Validation error getting due flashcards for user {user_id}: {str(e)}"
            )
            raise
        except Exception as e:
            logger.error(f"Error getting due flashcards for user {user_id}: {str(e)}")
            raise
