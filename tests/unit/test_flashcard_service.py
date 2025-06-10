import pytest
import uuid
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.services.flashcard_service import FlashcardService
from src.api.v1.schemas.flashcard_schemas import (
    ListFlashcardsQueryParams,
    FlashcardStatusEnum,
    FlashcardSourceEnum
)


class TestFlashcardServiceGetFlashcardsForUser:
    """Test suite for FlashcardService.get_flashcards_for_user method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_supabase = Mock()
        self.service = FlashcardService(self.mock_supabase)
        self.user_id = uuid.uuid4()
        self.sample_flashcards = [
            {
                "id": str(uuid.uuid4()),
                "user_id": str(self.user_id),
                "source_text_id": None,
                "front_content": "Question 1",
                "back_content": "Answer 1",
                "source": "manual",
                "status": "active",
                "created_at": "2024-01-01T00:00:00.000Z",
                "updated_at": "2024-01-01T00:00:00.000Z"
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": str(self.user_id),
                "source_text_id": str(uuid.uuid4()),
                "front_content": "Question 2",
                "back_content": "Answer 2",
                "source": "ai_suggestion",
                "status": "active",
                "created_at": "2024-01-01T01:00:00.000Z",
                "updated_at": "2024-01-01T01:00:00.000Z"
            }
        ]

    def test_get_flashcards_default_params(self):
        """Test getting flashcards with default parameters."""
        # Arrange
        params = ListFlashcardsQueryParams()
        
        # Mock chain methods
        mock_table = Mock()
        mock_select = Mock()
        mock_eq_user = Mock()
        mock_eq_status = Mock()
        mock_limit = Mock()
        mock_offset = Mock()
        mock_order = Mock()
        mock_execute = Mock()
        
        # Count query chain
        mock_count_select = Mock()
        mock_count_eq_user = Mock()
        mock_count_eq_status = Mock()
        mock_count_execute = Mock()
        
        # Setup method chaining for main query
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq_user
        mock_eq_user.eq.return_value = mock_eq_status
        mock_eq_status.limit.return_value = mock_limit
        mock_limit.offset.return_value = mock_offset
        mock_offset.order.return_value = mock_order
        mock_order.execute.return_value = mock_execute
        mock_execute.data = self.sample_flashcards

        # Setup method chaining for count query
        mock_table.select.side_effect = [mock_select, mock_count_select]
        mock_count_select.eq.return_value = mock_count_eq_user
        mock_count_eq_user.eq.return_value = mock_count_eq_status
        mock_count_eq_status.execute.return_value = mock_count_execute
        mock_count_execute.count = 2

        # Act
        result = self.service.get_flashcards_for_user(self.user_id, params)

        # Assert
        assert result.total == 2
        assert result.page == 1
        assert result.size == 20
        assert result.pages == 1
        assert len(result.items) == 2
        assert result.items[0].front_content == "Question 1"
        assert result.items[1].front_content == "Question 2"

    def test_get_flashcards_with_filters(self):
        """Test getting flashcards with status and source filters."""
        # Arrange
        params = ListFlashcardsQueryParams(
            status=FlashcardStatusEnum.PENDING_REVIEW,
            source=FlashcardSourceEnum.AI_SUGGESTION,
            page=1,
            size=10
        )
        
        # Mock similar to above but simplified for this test
        mock_response = Mock()
        mock_response.data = []
        mock_count_response = Mock()
        mock_count_response.count = 0
        
        # Setup mocking chain (simplified)
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.limit.return_value.offset.return_value.order.return_value.execute.return_value = mock_response
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_count_response

        # Act
        result = self.service.get_flashcards_for_user(self.user_id, params)

        # Assert
        assert result.total == 0
        assert result.page == 1
        assert result.size == 10
        assert result.pages == 1
        assert len(result.items) == 0

    def test_get_flashcards_pagination(self):
        """Test flashcards pagination calculation."""
        # Arrange
        params = ListFlashcardsQueryParams(page=2, size=5)
        
        mock_response = Mock()
        mock_response.data = []
        mock_count_response = Mock()
        mock_count_response.count = 12  # Total of 12 items
        
        # Setup mocking
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.offset.return_value.order.return_value.execute.return_value = mock_response
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_count_response

        # Act
        result = self.service.get_flashcards_for_user(self.user_id, params)

        # Assert
        assert result.total == 12
        assert result.page == 2
        assert result.size == 5
        assert result.pages == 3  # ceil(12/5) = 3

    def test_get_flashcards_empty_result(self):
        """Test handling empty flashcards result."""
        # Arrange
        params = ListFlashcardsQueryParams()
        
        mock_response = Mock()
        mock_response.data = None  # Supabase returns None for empty results
        mock_count_response = Mock()
        mock_count_response.count = 0
        
        # Setup mocking
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.offset.return_value.order.return_value.execute.return_value = mock_response
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_count_response

        # Act
        result = self.service.get_flashcards_for_user(self.user_id, params)

        # Assert
        assert result.total == 0
        assert len(result.items) == 0
        assert result.pages == 1

    def test_get_flashcards_database_error(self):
        """Test handling database errors."""
        # Arrange
        params = ListFlashcardsQueryParams()
        
        # Mock database error
        self.mock_supabase.table.side_effect = Exception("Database connection error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.service.get_flashcards_for_user(self.user_id, params)
        
        assert "Database connection error" in str(exc_info.value)


class TestFlashcardServiceUpdateFlashcard:
    """Test suite for FlashcardService.update_flashcard method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_supabase = Mock()
        self.service = FlashcardService(self.mock_supabase)
        self.user_id = uuid.uuid4()
        self.flashcard_id = uuid.uuid4()
        self.sample_flashcard = {
            "id": str(self.flashcard_id),
            "user_id": str(self.user_id),
            "source_text_id": None,
            "front_content": "Original question",
            "back_content": "Original answer",
            "source": "manual",
            "status": "active",
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-01T00:00:00.000Z"
        }

    def test_update_flashcard_content_success(self):
        """Test successful content update of a flashcard."""
        # Arrange
        updates = {
            "front_content": "Updated question",
            "back_content": "Updated answer"
        }
        
        # Mock current flashcard retrieval
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        
        # Mock update response
        updated_flashcard = self.sample_flashcard.copy()
        updated_flashcard.update(updates)
        updated_flashcard["updated_at"] = "2024-01-01T01:00:00.000Z"
        
        mock_update_response = Mock()
        mock_update_response.data = [updated_flashcard]
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        
        # First call for getting current flashcard
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Second call for updating flashcard
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_response
        
        # Act
        result = self.service.update_flashcard(self.flashcard_id, self.user_id, updates)
        
        # Assert
        assert result is not None
        assert result["front_content"] == "Updated question"
        assert result["back_content"] == "Updated answer"

    def test_update_flashcard_ai_status_to_active(self):
        """Test updating AI suggestion flashcard status from pending_review to active."""
        # Arrange
        ai_flashcard = self.sample_flashcard.copy()
        ai_flashcard.update({
            "source": "ai_suggestion",
            "status": "pending_review",
            "source_text_id": str(uuid.uuid4())
        })
        
        updates = {"status": "active"}
        
        # Mock responses
        mock_get_response = Mock()
        mock_get_response.data = [ai_flashcard]
        
        updated_flashcard = ai_flashcard.copy()
        updated_flashcard["status"] = "active"
        mock_update_response = Mock()
        mock_update_response.data = [updated_flashcard]
        
        # Mock AI generation event update
        mock_ai_event = {
            "id": str(uuid.uuid4()),
            "accepted_cards_count": 0,
            "rejected_cards_count": 0
        }
        mock_ai_event_response = Mock()
        mock_ai_event_response.data = [mock_ai_event]
        
        mock_ai_update_response = Mock()
        mock_ai_update_response.data = [{"accepted_cards_count": 1}]
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        
        # Mock call sequence
        call_count = 0
        def mock_table_calls(table_name):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First two calls for flashcard operations
                mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
                mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = mock_update_response
            else:  # Subsequent calls for AI event operations
                mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_ai_event_response
                mock_table.update.return_value.eq.return_value.execute.return_value = mock_ai_update_response
            return mock_table
        
        self.mock_supabase.table.side_effect = mock_table_calls
        
        # Act
        result = self.service.update_flashcard(self.flashcard_id, self.user_id, updates)
        
        # Assert
        assert result is not None
        assert result["status"] == "active"

    def test_update_flashcard_invalid_status_transition(self):
        """Test invalid status transition raises ValueError."""
        # Arrange
        updates = {"status": "rejected"}  # Manual flashcards can't have rejected status
        
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        
        # Setup method chaining
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.update_flashcard(self.flashcard_id, self.user_id, updates)
        
        assert "Invalid status transition" in str(exc_info.value)

    def test_update_flashcard_content_too_long(self):
        """Test content length validation."""
        # Arrange
        updates = {"front_content": "x" * 501}  # Exceeds 500 char limit
        
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.update_flashcard(self.flashcard_id, self.user_id, updates)
        
        assert "exceeds maximum length" in str(exc_info.value)

    def test_update_flashcard_malicious_content(self):
        """Test protection against malicious content."""
        # Arrange
        updates = {"front_content": "What is <script>alert('xss')</script>?"}
        
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.update_flashcard(self.flashcard_id, self.user_id, updates)
        
        assert "potentially unsafe content" in str(exc_info.value)

    def test_update_flashcard_empty_updates(self):
        """Test that empty updates dictionary raises ValueError."""
        # Arrange
        updates = {}
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.update_flashcard(self.flashcard_id, self.user_id, updates)
        
        assert "At least one field must be provided" in str(exc_info.value)

    def test_update_flashcard_not_found(self):
        """Test updating non-existent flashcard returns None."""
        # Arrange
        updates = {"front_content": "New content"}
        
        mock_get_response = Mock()
        mock_get_response.data = []  # Empty result
        
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Act
        result = self.service.update_flashcard(self.flashcard_id, self.user_id, updates)
        
        # Assert
        assert result is None

    def test_update_flashcard_invalid_enum_status(self):
        """Test invalid enum status value raises ValueError."""
        # Arrange
        updates = {"status": "invalid_status"}
        
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.update_flashcard(self.flashcard_id, self.user_id, updates)
        
        assert "Invalid status" in str(exc_info.value)
        assert "invalid_status" in str(exc_info.value)


class TestFlashcardServiceDeleteFlashcard:
    """Test suite for FlashcardService.delete_flashcard_by_id method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_supabase = Mock()
        self.service = FlashcardService(self.mock_supabase)
        self.user_id = uuid.uuid4()
        self.flashcard_id = uuid.uuid4()
        self.sample_flashcard = {
            "id": str(self.flashcard_id),
            "user_id": str(self.user_id),
            "source_text_id": None,
            "front_content": "Question to delete",
            "back_content": "Answer to delete",
            "source": "manual",
            "status": "active",
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-01T00:00:00.000Z"
        }

    def test_delete_flashcard_success(self):
        """Test successful deletion of a flashcard."""
        # Arrange
        # Mock current flashcard retrieval (ownership verification)
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        
        # Mock delete response (Supabase returns deleted record)
        mock_delete_response = Mock()
        mock_delete_response.data = [self.sample_flashcard]
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        
        # First call for getting current flashcard (ownership verification)
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Second call for deleting flashcard
        mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_delete_response
        
        # Act
        result = self.service.delete_flashcard_by_id(self.flashcard_id, self.user_id)
        
        # Assert
        assert result is True

    def test_delete_flashcard_not_found(self):
        """Test deleting non-existent flashcard returns False."""
        # Arrange
        mock_get_response = Mock()
        mock_get_response.data = []  # Empty result - flashcard not found
        
        # Setup method chaining
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Act
        result = self.service.delete_flashcard_by_id(self.flashcard_id, self.user_id)
        
        # Assert
        assert result is False

    def test_delete_flashcard_wrong_user(self):
        """Test that user can't delete another user's flashcard."""
        # Arrange
        other_user_flashcard = self.sample_flashcard.copy()
        other_user_flashcard["user_id"] = str(uuid.uuid4())  # Different user
        
        mock_get_response = Mock()
        mock_get_response.data = [other_user_flashcard]
        
        # Setup method chaining
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        
        # Act
        result = self.service.delete_flashcard_by_id(self.flashcard_id, self.user_id)
        
        # Assert
        assert result is False

    def test_delete_flashcard_invalid_user_id(self):
        """Test that invalid user ID raises ValueError."""
        # Arrange
        invalid_user_id = None
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.delete_flashcard_by_id(self.flashcard_id, invalid_user_id)
        
        assert "User ID is required" in str(exc_info.value)

    def test_delete_flashcard_invalid_flashcard_id(self):
        """Test that invalid flashcard ID raises ValueError."""
        # Arrange
        invalid_flashcard_id = None
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.delete_flashcard_by_id(invalid_flashcard_id, self.user_id)
        
        assert "Flashcard ID is required" in str(exc_info.value)

    def test_delete_flashcard_nil_uuid(self):
        """Test that nil UUID user ID raises ValueError."""
        # Arrange
        nil_uuid = uuid.UUID('00000000-0000-0000-0000-000000000000')
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.service.delete_flashcard_by_id(self.flashcard_id, nil_uuid)
        
        assert "Invalid user ID provided" in str(exc_info.value)

    def test_delete_flashcard_database_error_during_verification(self):
        """Test handling database error during ownership verification."""
        # Arrange
        self.mock_supabase.table.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.service.delete_flashcard_by_id(self.flashcard_id, self.user_id)
        
        assert "Database connection error" in str(exc_info.value)

    def test_delete_flashcard_deletion_operation_no_effect(self):
        """Test handling case where DELETE operation affects no records."""
        # Arrange
        # Mock successful ownership verification
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        
        # Mock DELETE operation with no effect (empty data array)
        mock_delete_response = Mock()
        mock_delete_response.data = []  # No records affected
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_delete_response
        
        # Act
        result = self.service.delete_flashcard_by_id(self.flashcard_id, self.user_id)
        
        # Assert
        assert result is False

    def test_delete_flashcard_wrong_record_deleted_security_error(self):
        """Test security error when wrong flashcard ID is returned from DELETE."""
        # Arrange
        # Mock successful ownership verification
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        
        # Mock DELETE operation returning wrong flashcard ID (security violation)
        wrong_flashcard = self.sample_flashcard.copy()
        wrong_flashcard["id"] = str(uuid.uuid4())  # Different ID
        mock_delete_response = Mock()
        mock_delete_response.data = [wrong_flashcard]
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_delete_response
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            self.service.delete_flashcard_by_id(self.flashcard_id, self.user_id)
        
        assert "Critical security error during deletion" in str(exc_info.value)

    def test_delete_ai_suggestion_flashcard_with_source_text(self):
        """Test deleting AI suggestion flashcard with source text ID."""
        # Arrange
        ai_flashcard = self.sample_flashcard.copy()
        ai_flashcard.update({
            "source": "ai_suggestion",
            "status": "active",
            "source_text_id": str(uuid.uuid4())
        })
        
        # Mock successful operations
        mock_get_response = Mock()
        mock_get_response.data = [ai_flashcard]
        
        mock_delete_response = Mock()
        mock_delete_response.data = [ai_flashcard]
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_get_response
        mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = mock_delete_response
        
        # Act
        result = self.service.delete_flashcard_by_id(self.flashcard_id, self.user_id)
        
        # Assert
        assert result is True 