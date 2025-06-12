import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import math
import time
import secrets

from supabase import Client
from src.api.v1.schemas.flashcard_schemas import (
    FlashcardManualCreateRequest, 
    ListFlashcardsQueryParams, 
    PaginatedFlashcardsResponse,
    FlashcardResponse
)
from src.db.schemas import FlashcardCreate, UserFlashcardSpacedRepetitionCreate, FlashcardSourceEnum, FlashcardStatusEnum
from src.db.flashcard_repository import FlashcardRepository

logger = logging.getLogger(__name__)

class FlashcardService:
    """Service for managing flashcard operations with enhanced security."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.repository = FlashcardRepository(supabase_client)
    
    def _add_timing_protection(self, min_time_ms: int = 100) -> None:
        """
        Add artificial delay to prevent timing attacks.
        
        Args:
            min_time_ms: Minimum time in milliseconds for operation
        """
        # Add random delay to prevent timing analysis
        delay = secrets.randbelow(50) + min_time_ms
        time.sleep(delay / 1000.0)
    
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
        if user_id == uuid.UUID('00000000-0000-0000-0000-000000000000'):
            raise ValueError("Invalid user ID provided")
    
    def create_manual_flashcard(
        self, 
        user_id: uuid.UUID, 
        data: FlashcardManualCreateRequest
    ) -> dict:
        """
        Create a manual flashcard with associated spaced repetition record.
        
        Args:
            user_id: UUID of the authenticated user
            data: Validated flashcard creation data
            
        Returns:
            Created flashcard data
            
        Raises:
            Exception: If database operations fail
        """
        try:
            # Prepare flashcard data
            flashcard_data = FlashcardCreate(
                user_id=user_id,
                front_content=data.front_content,
                back_content=data.back_content,
                source=FlashcardSourceEnum.MANUAL,
                status=FlashcardStatusEnum.ACTIVE,
                source_text_id=None
            )
            
            # Insert flashcard
            flashcard_response = self.supabase.table("flashcards").insert(
                flashcard_data.model_dump(exclude_unset=True, mode='json')
            ).execute()
            
            if not flashcard_response.data:
                raise Exception("Failed to create flashcard")
            
            created_flashcard = flashcard_response.data[0]
            flashcard_id = created_flashcard["id"]
            
            # Prepare spaced repetition data
            spaced_repetition_data = UserFlashcardSpacedRepetitionCreate(
                user_id=user_id,
                flashcard_id=uuid.UUID(flashcard_id),
                due_date=datetime.utcnow(),  # Ready for first review
                current_interval=1,
                last_reviewed_at=None
            )
            
            # Insert spaced repetition record
            spaced_rep_response = self.supabase.table("user_flashcard_spaced_repetition").insert(
                spaced_repetition_data.model_dump(exclude_unset=True, mode='json')
            ).execute()
            
            if not spaced_rep_response.data:
                # If spaced repetition fails, we should rollback flashcard creation
                # Note: Supabase doesn't support manual transactions, but RLS policies
                # should prevent inconsistent state
                logger.error(f"Failed to create spaced repetition record for flashcard {flashcard_id}")
                raise Exception("Failed to initialize spaced repetition for flashcard")
            
            logger.info(f"Successfully created manual flashcard {flashcard_id} for user {user_id}")
            return created_flashcard
            
        except Exception as e:
            logger.error(f"Error creating manual flashcard for user {user_id}: {str(e)}")
            raise

    def get_flashcards_for_user(
        self, 
        user_id: uuid.UUID, 
        params: ListFlashcardsQueryParams
    ) -> PaginatedFlashcardsResponse:
        """
        Get paginated list of flashcards for a user with optional filtering.
        
        Args:
            user_id: UUID of the authenticated user
            params: Query parameters for filtering and pagination
            
        Returns:
            PaginatedFlashcardsResponse with flashcards and metadata
            
        Raises:
            Exception: If database operations fail
        """
        try:
            # Build query with user_id filter (RLS will enforce this too)
            query = self.supabase.table("flashcards").select("*").eq("user_id", str(user_id))
            count_query = self.supabase.table("flashcards").select("id", count="exact").eq("user_id", str(user_id))
            
            # Apply status filter
            if params.status:
                query = query.eq("status", params.status.value)
                count_query = count_query.eq("status", params.status.value)
            
            # Apply source filter
            if params.source:
                query = query.eq("source", params.source.value)
                count_query = count_query.eq("source", params.source.value)
            
            # Get total count for pagination metadata
            count_response = count_query.execute()
            total = count_response.count if count_response.count is not None else 0
            
            # Apply pagination
            offset = (params.page - 1) * params.size
            query = query.limit(params.size).offset(offset)
            
            # Order by created_at desc for consistent pagination
            query = query.order("created_at", desc=True)
            
            # Execute main query
            flashcards_response = query.execute()
            
            if not flashcards_response.data:
                flashcards_data = []
            else:
                flashcards_data = flashcards_response.data
            
            # Convert to response models
            flashcards = [FlashcardResponse(**flashcard) for flashcard in flashcards_data]
            
            # Calculate pages
            pages = math.ceil(total / params.size) if total > 0 else 1
            
            logger.info(f"Retrieved {len(flashcards)} flashcards for user {user_id} (page {params.page}/{pages})")
            
            return PaginatedFlashcardsResponse(
                items=flashcards,
                total=total,
                page=params.page,
                size=params.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error retrieving flashcards for user {user_id}: {str(e)}")
            raise

    def get_flashcard_by_id(
        self, 
        flashcard_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> Optional[dict]:
        """
        Get a specific flashcard by ID for a user with enhanced security.
        
        Args:
            flashcard_id: UUID of the flashcard to retrieve
            user_id: UUID of the authenticated user
            
        Returns:
            Flashcard data if found and user has access, None otherwise
            
        Raises:
            Exception: If database operations fail
            ValueError: If input validation fails
        """
        start_time = time.time()
        
        try:
            # Enhanced security validation
            self._validate_user_access(user_id)
            
            if not flashcard_id:
                raise ValueError("Flashcard ID is required")
            
            # Security logging for audit trail
            logger.info(f"Flashcard access attempt: user={user_id}, flashcard={flashcard_id}")
            
            # Query flashcard with enhanced security filters
            # Double-check user ownership even with RLS
            query = (self.supabase.table("flashcards")
                    .select("*")
                    .eq("id", str(flashcard_id))
                    .eq("user_id", str(user_id))
                    .limit(1))  # Explicit limit for security
            
            # Execute query
            flashcard_response = query.execute()
            
            # Consistent timing to prevent enumeration attacks
            elapsed_time = (time.time() - start_time) * 1000
            if elapsed_time < 100:  # Ensure minimum response time
                self._add_timing_protection(100 - int(elapsed_time))
            
            if not flashcard_response.data:
                logger.info(f"Flashcard {flashcard_id} not found or not accessible by user {user_id}")
                return None
            
            flashcard_data = flashcard_response.data[0]
            
            # Additional security validation of returned data
            if flashcard_data.get('user_id') != str(user_id):
                logger.warning(f"Security violation: RLS bypass attempt detected for user {user_id}, flashcard {flashcard_id}")
                return None
            
            logger.info(f"Successfully retrieved flashcard {flashcard_id} for user {user_id}")
            return flashcard_data
            
        except ValueError as e:
            logger.warning(f"Input validation failed for flashcard retrieval: {str(e)}")
            self._add_timing_protection()  # Consistent timing even for errors
            raise
        except Exception as e:
            logger.error(f"Error retrieving flashcard {flashcard_id} for user {user_id}: {str(e)}")
            self._add_timing_protection()  # Consistent timing even for errors
            raise

    def update_flashcard(
        self, 
        flashcard_id: uuid.UUID, 
        user_id: uuid.UUID, 
        updates: dict
    ) -> Optional[dict]:
        """
        Update a flashcard's content or status with enhanced security and validation.
        
        Args:
            flashcard_id: UUID of the flashcard to update
            user_id: UUID of the authenticated user
            updates: Dictionary containing fields to update
            
        Returns:
            Updated flashcard data if successful, None if not found
            
        Raises:
            ValueError: If validation fails
            Exception: If database operations fail
        """
        start_time = time.time()
        
        try:
            # Enhanced security validation
            self._validate_user_access(user_id)
            
            if not flashcard_id:
                raise ValueError("Flashcard ID is required")
            
            if not updates:
                raise ValueError("At least one field must be provided for update")
            
            # Security logging for audit trail
            logger.info(f"Flashcard update attempt: user={user_id}, flashcard={flashcard_id}, fields={list(updates.keys())}")
            
            # First, get the current flashcard to validate ownership and current state
            current_flashcard_response = (self.supabase.table("flashcards")
                                        .select("*")
                                        .eq("id", str(flashcard_id))
                                        .eq("user_id", str(user_id))
                                        .limit(1)
                                        .execute())
            
            if not current_flashcard_response.data:
                logger.info(f"Flashcard {flashcard_id} not found or not accessible by user {user_id}")
                return None
            
            current_flashcard = current_flashcard_response.data[0]
            
            # Validate business rules for status transitions
            if 'status' in updates:
                new_status = updates['status']
                current_status = current_flashcard.get('status')
                current_source = current_flashcard.get('source')
                
                # Validate status transition rules
                if not self._validate_status_transition(current_source, current_status, new_status):
                    raise ValueError(f"Invalid status transition from {current_status} to {new_status} for {current_source} flashcard")
                
                # For AI suggestions, prepare to update generation event statistics
                if current_source == 'ai_suggestion' and current_status != new_status:
                    self._should_update_ai_stats = {
                        'source_text_id': current_flashcard.get('source_text_id'),
                        'old_status': current_status,
                        'new_status': new_status
                    }
            
            # Enhanced content validation
            if 'front_content' in updates:
                front_content = updates['front_content']
                if len(front_content) > 500:
                    raise ValueError("Front content exceeds maximum length of 500 characters")
                if len(front_content.strip()) == 0:
                    raise ValueError("Front content cannot be empty")
                # Additional validation for malicious content
                if any(char in front_content for char in ['<script', '<iframe', 'javascript:']):
                    raise ValueError("Front content contains potentially unsafe content")
            
            if 'back_content' in updates:
                back_content = updates['back_content']
                if len(back_content) > 1000:
                    raise ValueError("Back content exceeds maximum length of 1000 characters")
                if len(back_content.strip()) == 0:
                    raise ValueError("Back content cannot be empty")
                # Additional validation for malicious content
                if any(char in back_content for char in ['<script', '<iframe', 'javascript:']):
                    raise ValueError("Back content contains potentially unsafe content")
            
            # Enhanced status validation
            if 'status' in updates:
                allowed_statuses = ['active', 'pending_review', 'rejected']
                self._validate_enum_values('status', updates['status'], allowed_statuses)
            
            # Add timestamp for update tracking
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            # Perform the update with security filters
            update_response = (self.supabase.table("flashcards")
                             .update(updates)
                             .eq("id", str(flashcard_id))
                             .eq("user_id", str(user_id))
                             .execute())
            
            if not update_response.data:
                logger.error(f"Failed to update flashcard {flashcard_id} for user {user_id}")
                raise Exception("Failed to update flashcard")
            
            updated_flashcard = update_response.data[0]
            
            # Update AI generation event statistics if needed
            if hasattr(self, '_should_update_ai_stats'):
                try:
                    self._update_ai_generation_stats(self._should_update_ai_stats)
                except Exception as e:
                    logger.warning(f"Failed to update AI generation stats for flashcard {flashcard_id}: {str(e)}")
                    # Don't fail the entire operation for stats update failure
                finally:
                    delattr(self, '_should_update_ai_stats')
            
            # Log successful update with performance metrics
            elapsed_time = (time.time() - start_time) * 1000
            logger.info(f"Successfully updated flashcard {flashcard_id} for user {user_id} in {round(elapsed_time, 2)}ms")
            
            return updated_flashcard
            
        except ValueError as e:
            logger.warning(f"Validation error updating flashcard {flashcard_id} for user {user_id}: {str(e)}")
            self._add_timing_protection()
            raise
        except Exception as e:
            logger.error(f"Error updating flashcard {flashcard_id} for user {user_id}: {str(e)}")
            self._add_timing_protection()
            raise

    def _validate_status_transition(self, source: str, current_status: str, new_status: str) -> bool:
        """
        Validate if status transition is allowed based on business rules.
        
        Args:
            source: Source of the flashcard ('manual' or 'ai_suggestion')
            current_status: Current status of the flashcard
            new_status: Requested new status
            
        Returns:
            True if transition is valid, False otherwise
        """
        # Manual flashcards can only have 'active' status
        if source == 'manual':
            return new_status == 'active'
        
        # AI suggestion flashcards have more complex rules
        if source == 'ai_suggestion':
            # From pending_review: can go to active or rejected
            if current_status == 'pending_review':
                return new_status in ['active', 'rejected']
            
            # From active: typically should stay active (could add more rules)
            if current_status == 'active':
                return new_status == 'active'
            
            # From rejected: typically should stay rejected (could add more rules)
            if current_status == 'rejected':
                return new_status == 'rejected'
        
        # Default: no transition allowed
        return False

    def update_flashcard_optimized(
        self, 
        flashcard_id: uuid.UUID, 
        user_id: uuid.UUID, 
        updates: dict
    ) -> Optional[dict]:
        """
        Optimized version of update_flashcard using repository pattern and single queries.
        
        Args:
            flashcard_id: UUID of the flashcard to update
            user_id: UUID of the authenticated user
            updates: Dictionary containing fields to update
            
        Returns:
            Updated flashcard data if successful, None if not found
            
        Raises:
            ValueError: If validation fails
            Exception: If database operations fail
        """
        start_time = time.time()
        
        try:
            # Enhanced security validation
            self._validate_user_access(user_id)
            
            if not flashcard_id:
                raise ValueError("Flashcard ID is required")
            
            if not updates:
                raise ValueError("At least one field must be provided for update")
            
            # Security logging for audit trail
            logger.info(f"Optimized flashcard update attempt: user={user_id}, flashcard={flashcard_id}, fields={list(updates.keys())}")
            
            # Single query to get current flashcard with ownership verification
            current_flashcard = self.repository.get_flashcard_by_id_and_user(flashcard_id, user_id)
            
            if not current_flashcard:
                logger.info(f"Flashcard {flashcard_id} not found or not accessible by user {user_id}")
                return None
            
            # Validate business rules for status transitions
            if 'status' in updates:
                new_status = updates['status']
                current_status = current_flashcard.get('status')
                current_source = current_flashcard.get('source')
                
                # Validate status transition rules
                if not self._validate_status_transition(current_source, current_status, new_status):
                    raise ValueError(f"Invalid status transition from {current_status} to {new_status} for {current_source} flashcard")
                
                # Prepare AI stats update if needed
                if current_source == 'ai_suggestion' and current_status != new_status:
                    source_text_id = current_flashcard.get('source_text_id')
                    if source_text_id:
                        try:
                            self._update_ai_generation_stats_optimized(
                                source_text_id, current_status, new_status
                            )
                        except Exception as e:
                            logger.warning(f"Failed to update AI generation stats: {str(e)}")
                            # Don't fail the entire operation for stats update failure
            
            # Enhanced content validation
            self._validate_content_updates(updates)
            
            # Enhanced status validation
            if 'status' in updates:
                allowed_statuses = ['active', 'pending_review', 'rejected']
                self._validate_enum_values('status', updates['status'], allowed_statuses)
            
            # Single optimized query for update with ownership check built-in
            updated_flashcard = self.repository.update_flashcard_optimized(
                flashcard_id, user_id, updates
            )
            
            if not updated_flashcard:
                logger.error(f"Failed to update flashcard {flashcard_id} for user {user_id}")
                raise Exception("Failed to update flashcard")
            
            # Log successful update with performance metrics
            elapsed_time = (time.time() - start_time) * 1000
            logger.info(f"Successfully updated flashcard {flashcard_id} for user {user_id} in {round(elapsed_time, 2)}ms")
            
            return updated_flashcard
            
        except ValueError as e:
            logger.warning(f"Validation error updating flashcard {flashcard_id} for user {user_id}: {str(e)}")
            self._add_timing_protection()
            raise
        except Exception as e:
            logger.error(f"Error updating flashcard {flashcard_id} for user {user_id}: {str(e)}")
            self._add_timing_protection()
            raise

    def _update_ai_generation_stats_optimized(
        self, 
        source_text_id: str, 
        old_status: str, 
        new_status: str
    ) -> None:
        """
        Optimized version of AI generation stats update using repository.
        
        Args:
            source_text_id: Source text UUID string
            old_status: Previous status
            new_status: New status
        """
        try:
            source_text_uuid = uuid.UUID(source_text_id)
            event = self.repository.get_ai_generation_event_by_source_text(source_text_uuid)
            
            if not event:
                logger.warning(f"AI generation event not found for source_text_id: {source_text_id}")
                return
            
            # Calculate counter updates
            updates = {}
            if old_status == 'pending_review' and new_status == 'active':
                updates['accepted_cards_count'] = event.get('accepted_cards_count', 0) + 1
            elif old_status == 'pending_review' and new_status == 'rejected':
                updates['rejected_cards_count'] = event.get('rejected_cards_count', 0) + 1
            elif old_status == 'active' and new_status == 'rejected':
                updates['accepted_cards_count'] = max(0, event.get('accepted_cards_count', 0) - 1)
                updates['rejected_cards_count'] = event.get('rejected_cards_count', 0) + 1
            elif old_status == 'rejected' and new_status == 'active':
                updates['rejected_cards_count'] = max(0, event.get('rejected_cards_count', 0) - 1)
                updates['accepted_cards_count'] = event.get('accepted_cards_count', 0) + 1
            
            if updates:
                event_id = uuid.UUID(event['id'])
                self.repository.update_ai_generation_event_stats(event_id, updates)
                logger.info(f"Updated AI generation stats for event {event_id}: {updates}")
                
        except Exception as e:
            logger.error(f"Error updating AI generation stats: {str(e)}")
            raise

    def _validate_content_updates(self, updates: dict) -> None:
        """
        Validate content fields in updates dictionary.
        
        Args:
            updates: Dictionary of updates to validate
            
        Raises:
            ValueError: If validation fails
        """
        if 'front_content' in updates:
            front_content = updates['front_content']
            if len(front_content) > 500:
                raise ValueError("Front content exceeds maximum length of 500 characters")
            if len(front_content.strip()) == 0:
                raise ValueError("Front content cannot be empty")
            # Additional validation for malicious content
            if any(char in front_content for char in ['<script', '<iframe', 'javascript:']):
                raise ValueError("Front content contains potentially unsafe content")
        
        if 'back_content' in updates:
            back_content = updates['back_content']
            if len(back_content) > 1000:
                raise ValueError("Back content exceeds maximum length of 1000 characters")
            if len(back_content.strip()) == 0:
                raise ValueError("Back content cannot be empty")
            # Additional validation for malicious content
            if any(char in back_content for char in ['<script', '<iframe', 'javascript:']):
                raise ValueError("Back content contains potentially unsafe content")

    def _update_ai_generation_stats(self, stats_data: dict) -> None:
        """
        Update AI generation event statistics when flashcard status changes.
        
        Args:
            stats_data: Dictionary containing source_text_id, old_status, new_status
        """
        try:
            source_text_id = stats_data['source_text_id']
            old_status = stats_data['old_status']
            new_status = stats_data['new_status']
            
            if not source_text_id:
                logger.warning("Cannot update AI stats: source_text_id is missing")
                return
            
            # Find the corresponding AI generation event
            event_response = (self.supabase.table("ai_generation_events")
                            .select("*")
                            .eq("source_text_id", str(source_text_id))
                            .limit(1)
                            .execute())
            
            if not event_response.data:
                logger.warning(f"AI generation event not found for source_text_id: {source_text_id}")
                return
            
            event = event_response.data[0]
            updates = {}
            
            # Handle status transitions and update counters accordingly
            if old_status == 'pending_review' and new_status == 'active':
                updates['accepted_cards_count'] = event.get('accepted_cards_count', 0) + 1
            elif old_status == 'pending_review' and new_status == 'rejected':
                updates['rejected_cards_count'] = event.get('rejected_cards_count', 0) + 1
            elif old_status == 'active' and new_status == 'rejected':
                # Card was accepted before, now rejected
                updates['accepted_cards_count'] = max(0, event.get('accepted_cards_count', 0) - 1)
                updates['rejected_cards_count'] = event.get('rejected_cards_count', 0) + 1
            elif old_status == 'rejected' and new_status == 'active':
                # Card was rejected before, now accepted
                updates['rejected_cards_count'] = max(0, event.get('rejected_cards_count', 0) - 1)
                updates['accepted_cards_count'] = event.get('accepted_cards_count', 0) + 1
            
            if updates:
                # Add timestamp for update tracking
                updates['updated_at'] = datetime.utcnow().isoformat()
                
                # Update the AI generation event
                update_response = (self.supabase.table("ai_generation_events")
                                 .update(updates)
                                 .eq("id", event['id'])
                                 .execute())
                
                if update_response.data:
                    logger.info(f"Updated AI generation stats for event {event['id']}: {updates}")
                else:
                    logger.error(f"Failed to update AI generation event {event['id']}")
                    
        except Exception as e:
            logger.error(f"Error updating AI generation stats: {str(e)}")
            raise

    def _validate_enum_values(self, field_name: str, value: str, allowed_values: list) -> bool:
        """
        Enhanced enum validation with detailed error messages.
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate
            allowed_values: List of allowed enum values
            
        Returns:
            True if value is valid
            
        Raises:
            ValueError: If value is not in allowed_values
        """
        if value not in allowed_values:
            raise ValueError(f"Invalid {field_name}: '{value}'. Allowed values are: {', '.join(allowed_values)}")
        return True

    def _validate_concurrent_update_protection(self, flashcard_id: uuid.UUID, expected_updated_at: datetime) -> bool:
        """
        Basic protection against concurrent updates (optimistic locking pattern).
        
        Args:
            flashcard_id: UUID of the flashcard
            expected_updated_at: Expected timestamp of last update
            
        Returns:
            True if timestamps match (safe to update)
            
        Raises:
            ValueError: If concurrent modification detected
        """
        current_response = (self.supabase.table("flashcards")
                          .select("updated_at")
                          .eq("id", str(flashcard_id))
                          .limit(1)
                          .execute())
        
        if not current_response.data:
            raise ValueError("Flashcard not found during concurrent update check")
        
        current_updated_at = current_response.data[0]['updated_at']
        
        # Compare timestamps (allowing small tolerance for millisecond differences)
        if isinstance(current_updated_at, str):
            current_updated_at = datetime.fromisoformat(current_updated_at.replace('Z', '+00:00'))
        
        time_diff = abs((current_updated_at - expected_updated_at).total_seconds())
        
        if time_diff > 1:  # More than 1 second difference indicates concurrent modification
            raise ValueError("Flashcard was modified by another process. Please refresh and try again.")
        
        return True

    def delete_flashcard_by_id(
        self, 
        flashcard_id: uuid.UUID, 
        user_id: uuid.UUID
    ) -> bool:
        """
        Delete a specific flashcard with enhanced security and validation.
        CASCADE operations automatically remove related spaced repetition data.
        
        Args:
            flashcard_id: UUID of the flashcard to delete
            user_id: UUID of the authenticated user
            
        Returns:
            True if flashcard was successfully deleted, False if not found
            
        Raises:
            ValueError: If input validation fails
            Exception: If database operations fail
        """
        start_time = time.time()
        
        try:
            # Enhanced security validation
            self._validate_user_access(user_id)
            
            if not flashcard_id:
                raise ValueError("Flashcard ID is required")
            
            # Security logging for audit trail
            logger.info(f"Flashcard delete attempt: user={user_id}, flashcard={flashcard_id}")
            
            # First verify ownership and existence with detailed security checks
            current_flashcard_response = (self.supabase.table("flashcards")
                                        .select("id, user_id, source, status, source_text_id")
                                        .eq("id", str(flashcard_id))
                                        .eq("user_id", str(user_id))
                                        .limit(1)
                                        .execute())
            
            if not current_flashcard_response.data:
                logger.info(f"Flashcard {flashcard_id} not found or not accessible by user {user_id}")
                return False
            
            current_flashcard = current_flashcard_response.data[0]
            
            # Additional security validation of returned data
            if current_flashcard.get('user_id') != str(user_id):
                logger.warning(f"Security violation: RLS bypass attempt detected for user {user_id}, flashcard {flashcard_id}")
                return False
            
            # Log flashcard details for audit trail before deletion
            logger.info(f"Deleting flashcard {flashcard_id}: source={current_flashcard.get('source')}, status={current_flashcard.get('status')}")
            
            # Perform the DELETE operation with security filters
            # RLS policies ensure user can only delete their own flashcards
            # CASCADE constraints automatically handle related spaced_repetition data
            delete_response = (self.supabase.table("flashcards")
                             .delete()
                             .eq("id", str(flashcard_id))
                             .eq("user_id", str(user_id))
                             .execute())
            
            # Check if deletion was successful
            # Supabase returns the deleted records, empty array means nothing was deleted
            if not delete_response.data:
                logger.warning(f"DELETE operation completed but no records affected for flashcard {flashcard_id}")
                return False
            
            deleted_flashcard = delete_response.data[0]
            deleted_flashcard_id = deleted_flashcard.get('id')
            
            # Verify the correct flashcard was deleted
            if deleted_flashcard_id != str(flashcard_id):
                logger.error(f"Security error: Wrong flashcard deleted! Expected {flashcard_id}, got {deleted_flashcard_id}")
                raise Exception("Critical security error during deletion")
            
            # Log successful deletion with performance metrics
            elapsed_time = (time.time() - start_time) * 1000
            logger.info(f"Successfully deleted flashcard {flashcard_id} for user {user_id} in {round(elapsed_time, 2)}ms")
            
            return True
            
        except ValueError as e:
            logger.warning(f"Input validation failed for flashcard deletion: {str(e)}")
            self._add_timing_protection()  # Consistent timing even for errors
            raise
        except Exception as e:
            logger.error(f"Error deleting flashcard {flashcard_id} for user {user_id}: {str(e)}")
            self._add_timing_protection()  # Consistent timing even for errors
            raise 