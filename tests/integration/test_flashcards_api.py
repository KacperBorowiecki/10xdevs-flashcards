import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from src.api.v1.schemas.flashcard_schemas import (
    FlashcardSourceEnum,
    FlashcardStatusEnum,
)


@pytest.mark.skip("TODO: Fix integration test authorization and mocking issues")
class TestFlashcardsListEndpoint:
    """Integration tests for GET /api/v1/flashcards endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.user_id = uuid.uuid4()
        self.valid_token = "valid_jwt_token"
        self.auth_headers = {"Authorization": f"Bearer {self.valid_token}"}

        self.sample_flashcards = [
            {
                "id": str(uuid.uuid4()),
                "user_id": str(self.user_id),
                "source_text_id": None,
                "front_content": "What is Python?",
                "back_content": "A programming language",
                "source": "manual",
                "status": "active",
                "created_at": "2024-01-01T00:00:00.000Z",
                "updated_at": "2024-01-01T00:00:00.000Z",
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": str(self.user_id),
                "source_text_id": str(uuid.uuid4()),
                "front_content": "What is FastAPI?",
                "back_content": "A modern web framework",
                "source": "ai_suggestion",
                "status": "active",
                "created_at": "2024-01-01T01:00:00.000Z",
                "updated_at": "2024-01-01T01:00:00.000Z",
            },
        ]

    @patch("src.db.supabase_client.get_supabase_client")
    def test_list_flashcards_success_with_defaults(self, mock_get_supabase):
        """Test successful flashcards listing with default parameters."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database response
        mock_query_response = Mock()
        mock_query_response.data = self.sample_flashcards
        mock_count_response = Mock()
        mock_count_response.count = 2

        # Setup method chaining
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.offset.return_value.order.return_value.execute.return_value = (
            mock_query_response
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_count_response
        )

        # Act
        response = self.client.get("/api/v1/flashcards", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 1
        assert len(data["items"]) == 2
        assert data["items"][0]["front_content"] == "What is Python?"
        assert data["items"][1]["front_content"] == "What is FastAPI?"

    @patch("src.db.supabase_client.get_supabase_client")
    def test_list_flashcards_with_query_params(self, mock_get_supabase):
        """Test flashcards listing with query parameters."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database response (empty for filtered results)
        mock_query_response = Mock()
        mock_query_response.data = []
        mock_count_response = Mock()
        mock_count_response.count = 0

        # Setup method chaining
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.limit.return_value.offset.return_value.order.return_value.execute.return_value = (
            mock_query_response
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_count_response
        )

        # Act
        response = self.client.get(
            "/api/v1/flashcards?status=pending_review&source=ai_suggestion&page=1&size=10",
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["pages"] == 1
        assert len(data["items"]) == 0

    @patch("src.db.supabase_client.get_supabase_client")
    def test_list_flashcards_pagination(self, mock_get_supabase):
        """Test flashcards listing with pagination."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database response
        mock_query_response = Mock()
        mock_query_response.data = [
            self.sample_flashcards[0]
        ]  # Second page with 1 item
        mock_count_response = Mock()
        mock_count_response.count = 25  # Total items

        # Setup method chaining
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.offset.return_value.order.return_value.execute.return_value = (
            mock_query_response
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_count_response
        )

        # Act
        response = self.client.get(
            "/api/v1/flashcards?page=2&size=20", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 25
        assert data["page"] == 2
        assert data["size"] == 20
        assert data["pages"] == 2  # ceil(25/20) = 2
        assert len(data["items"]) == 1

    def test_list_flashcards_unauthorized_no_token(self):
        """Test flashcards listing without authentication token."""
        # Act
        response = self.client.get("/api/v1/flashcards")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("src.db.supabase_client.get_supabase_client")
    def test_list_flashcards_unauthorized_invalid_token(self, mock_get_supabase):
        """Test flashcards listing with invalid authentication token."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth failure
        mock_user_response = Mock()
        mock_user_response.user = None
        mock_supabase.auth.get_user.return_value = mock_user_response

        invalid_headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response = self.client.get("/api/v1/flashcards", headers=invalid_headers)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in response.json()["detail"]

    def test_list_flashcards_invalid_query_params(self):
        """Test flashcards listing with invalid query parameters."""
        # Act - Invalid page (< 1)
        response = self.client.get(
            "/api/v1/flashcards?page=0", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Act - Invalid size (> 100)
        response = self.client.get(
            "/api/v1/flashcards?size=150", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Act - Invalid status
        response = self.client.get(
            "/api/v1/flashcards?status=invalid_status", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("src.db.supabase_client.get_supabase_client")
    def test_list_flashcards_database_error(self, mock_get_supabase):
        """Test flashcards listing with database error."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database error
        mock_supabase.table.side_effect = Exception("Database connection error")

        # Act
        response = self.client.get("/api/v1/flashcards", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal server error" in response.json()["detail"]

    @patch("src.db.supabase_client.get_supabase_client")
    def test_list_flashcards_empty_result(self, mock_get_supabase):
        """Test flashcards listing with empty result."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock empty database response
        mock_query_response = Mock()
        mock_query_response.data = None
        mock_count_response = Mock()
        mock_count_response.count = 0

        # Setup method chaining
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.offset.return_value.order.return_value.execute.return_value = (
            mock_query_response
        )
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_count_response
        )

        # Act
        response = self.client.get("/api/v1/flashcards", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 1
        assert len(data["items"]) == 0


@pytest.mark.skip("TODO: Fix integration test authorization and mocking issues")
class TestFlashcardsUpdateEndpoint:
    """Integration tests for PATCH /api/v1/flashcards/{flashcard_id} endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.user_id = uuid.uuid4()
        self.flashcard_id = uuid.uuid4()
        self.other_user_id = uuid.uuid4()
        self.valid_token = "valid_jwt_token"
        self.auth_headers = {"Authorization": f"Bearer {self.valid_token}"}

        self.sample_flashcard = {
            "id": str(self.flashcard_id),
            "user_id": str(self.user_id),
            "source_text_id": None,
            "front_content": "What is Python?",
            "back_content": "A programming language",
            "source": "manual",
            "status": "active",
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-01T00:00:00.000Z",
        }

    @patch("src.db.supabase_client.get_supabase_client")
    def test_update_flashcard_content_success(self, mock_get_supabase):
        """Test successful flashcard content update."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock get current flashcard
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]

        # Mock update response
        updated_flashcard = self.sample_flashcard.copy()
        updated_flashcard.update(
            {
                "front_content": "What is Python programming?",
                "back_content": "A high-level programming language",
                "updated_at": "2024-01-01T01:00:00.000Z",
            }
        )
        mock_update_response = Mock()
        mock_update_response.data = [updated_flashcard]

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_update_response
        )

        update_data = {
            "front_content": "What is Python programming?",
            "back_content": "A high-level programming language",
        }

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json=update_data,
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["front_content"] == "What is Python programming?"
        assert data["back_content"] == "A high-level programming language"
        assert data["id"] == str(self.flashcard_id)

    @patch("src.db.supabase_client.get_supabase_client")
    def test_update_flashcard_ai_status_to_active(self, mock_get_supabase):
        """Test updating AI suggestion flashcard status from pending_review to active."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # AI flashcard with pending_review status
        ai_flashcard = self.sample_flashcard.copy()
        ai_flashcard.update(
            {
                "source": "ai_suggestion",
                "status": "pending_review",
                "source_text_id": str(uuid.uuid4()),
            }
        )

        # Mock get current flashcard
        mock_get_response = Mock()
        mock_get_response.data = [ai_flashcard]

        # Mock update response
        updated_flashcard = ai_flashcard.copy()
        updated_flashcard["status"] = "active"
        mock_update_response = Mock()
        mock_update_response.data = [updated_flashcard]

        # Mock AI generation event
        mock_ai_event_response = Mock()
        mock_ai_event_response.data = [
            {
                "id": str(uuid.uuid4()),
                "accepted_cards_count": 0,
                "rejected_cards_count": 0,
            }
        ]
        mock_ai_update_response = Mock()
        mock_ai_update_response.data = [{"accepted_cards_count": 1}]

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table

        # Flashcard operations
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )
        mock_table.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_update_response
        )

        # AI event operations (simplified mocking)
        mock_table.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_ai_event_response
        )
        mock_table.update.return_value.eq.return_value.execute.return_value = (
            mock_ai_update_response
        )

        update_data = {"status": "active"}

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json=update_data,
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "active"
        assert data["source"] == "ai_suggestion"

    @patch("src.db.supabase_client.get_supabase_client")
    def test_update_flashcard_not_found(self, mock_get_supabase):
        """Test updating non-existent flashcard returns 404."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock empty response (flashcard not found)
        mock_get_response = Mock()
        mock_get_response.data = []

        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )

        update_data = {"front_content": "Updated content"}

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json=update_data,
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_update_flashcard_unauthorized_no_token(self):
        """Test updating flashcard without authentication token."""
        # Arrange
        update_data = {"front_content": "Updated content"}

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}", json=update_data
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("src.db.supabase_client.get_supabase_client")
    def test_update_flashcard_unauthorized_invalid_token(self, mock_get_supabase):
        """Test updating flashcard with invalid authentication token."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth failure
        mock_user_response = Mock()
        mock_user_response.user = None
        mock_supabase.auth.get_user.return_value = mock_user_response

        invalid_headers = {"Authorization": "Bearer invalid_token"}
        update_data = {"front_content": "Updated content"}

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json=update_data,
            headers=invalid_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_flashcard_invalid_uuid(self):
        """Test updating flashcard with invalid UUID format."""
        # Arrange
        invalid_id = "not-a-uuid"
        update_data = {"front_content": "Updated content"}

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{invalid_id}",
            json=update_data,
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_flashcard_empty_request_body(self):
        """Test updating flashcard with empty request body."""
        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json={},
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "At least one field must be provided" in response.json()["detail"]

    def test_update_flashcard_content_too_long(self):
        """Test updating flashcard with content exceeding length limits."""
        # Arrange
        update_data = {"front_content": "x" * 501}  # Exceeds 500 char limit

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json=update_data,
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("src.db.supabase_client.get_supabase_client")
    def test_update_flashcard_invalid_status_transition(self, mock_get_supabase):
        """Test updating flashcard with invalid status transition."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock get current flashcard (manual flashcard)
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]

        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )

        # Try to set manual flashcard to rejected status (invalid)
        update_data = {"status": "rejected"}

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json=update_data,
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid status transition" in response.json()["detail"]

    def test_update_flashcard_invalid_status_enum(self):
        """Test updating flashcard with invalid status enum value."""
        # Arrange
        update_data = {"status": "invalid_status"}

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json=update_data,
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("src.db.supabase_client.get_supabase_client")
    def test_update_flashcard_malicious_content(self, mock_get_supabase):
        """Test updating flashcard with potentially malicious content."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock get current flashcard
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]

        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )

        update_data = {"front_content": "What is <script>alert('xss')</script>?"}

        # Act
        response = self.client.patch(
            f"/api/v1/flashcards/{self.flashcard_id}",
            json=update_data,
            headers=self.auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "potentially unsafe content" in response.json()["detail"]


@pytest.mark.skip("TODO: Fix integration test authorization and mocking issues")
class TestFlashcardsDeleteEndpoint:
    """Integration tests for DELETE /api/v1/flashcards/{flashcard_id} endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.user_id = uuid.uuid4()
        self.flashcard_id = uuid.uuid4()
        self.other_user_id = uuid.uuid4()
        self.valid_token = "valid_jwt_token"
        self.auth_headers = {"Authorization": f"Bearer {self.valid_token}"}

        self.sample_flashcard = {
            "id": str(self.flashcard_id),
            "user_id": str(self.user_id),
            "source_text_id": None,
            "front_content": "What is Python?",
            "back_content": "A programming language",
            "source": "manual",
            "status": "active",
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-01T00:00:00.000Z",
        }

    @patch("src.db.supabase_client.get_supabase_client")
    def test_delete_flashcard_success(self, mock_get_supabase):
        """Test successful flashcard deletion."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock ownership verification (GET operation)
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]

        # Mock delete operation (returns deleted record)
        mock_delete_response = Mock()
        mock_delete_response.data = [self.sample_flashcard]

        # Setup method chaining with separate table mock instances
        mock_table_get = Mock()
        mock_table_delete = Mock()

        # Use side_effect to return different mocks for different table calls
        mock_supabase.table.side_effect = [mock_table_get, mock_table_delete]

        # Setup GET operation chain
        mock_table_get.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )

        # Setup DELETE operation chain
        mock_table_delete.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_delete_response
        )

        # Act
        response = self.client.delete(
            f"/api/v1/flashcards/{self.flashcard_id}", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.text == ""  # Empty body for 204 response

    @patch("src.db.supabase_client.get_supabase_client")
    def test_delete_flashcard_not_found(self, mock_get_supabase):
        """Test deleting non-existent flashcard returns 404."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock ownership verification returning empty result (not found)
        mock_get_response = Mock()
        mock_get_response.data = []

        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )

        # Act
        response = self.client.delete(
            f"/api/v1/flashcards/{self.flashcard_id}", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_delete_flashcard_unauthorized_no_token(self):
        """Test deleting flashcard without authentication token."""
        # Act
        response = self.client.delete(f"/api/v1/flashcards/{self.flashcard_id}")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("src.db.supabase_client.get_supabase_client")
    def test_delete_flashcard_unauthorized_invalid_token(self, mock_get_supabase):
        """Test deleting flashcard with invalid authentication token."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth failure
        mock_user_response = Mock()
        mock_user_response.user = None
        mock_supabase.auth.get_user.return_value = mock_user_response

        invalid_headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response = self.client.delete(
            f"/api/v1/flashcards/{self.flashcard_id}", headers=invalid_headers
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_flashcard_invalid_uuid(self):
        """Test deleting flashcard with invalid UUID format."""
        # Arrange
        invalid_id = "not-a-uuid"

        # Act
        response = self.client.delete(
            f"/api/v1/flashcards/{invalid_id}", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_flashcard_nil_uuid(self):
        """Test deleting flashcard with nil UUID (all zeros)."""
        # Arrange
        nil_uuid = "00000000-0000-0000-0000-000000000000"

        # Act
        response = self.client.delete(
            f"/api/v1/flashcards/{nil_uuid}", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Empty UUID is not allowed" in response.json()["detail"]

    @patch("src.db.supabase_client.get_supabase_client")
    def test_delete_flashcard_database_error(self, mock_get_supabase):
        """Test deleting flashcard with database error."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database error
        mock_supabase.table.side_effect = Exception("Database connection error")

        # Act
        response = self.client.delete(
            f"/api/v1/flashcards/{self.flashcard_id}", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal server error" in response.json()["detail"]

    @patch("src.db.supabase_client.get_supabase_client")
    def test_delete_ai_suggestion_flashcard(self, mock_get_supabase):
        """Test deleting AI suggestion flashcard succeeds."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # AI suggestion flashcard
        ai_flashcard = self.sample_flashcard.copy()
        ai_flashcard.update(
            {
                "source": "ai_suggestion",
                "status": "active",
                "source_text_id": str(uuid.uuid4()),
            }
        )

        # Mock ownership verification
        mock_get_response = Mock()
        mock_get_response.data = [ai_flashcard]

        # Mock delete operation
        mock_delete_response = Mock()
        mock_delete_response.data = [ai_flashcard]

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )
        mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_delete_response
        )

        # Act
        response = self.client.delete(
            f"/api/v1/flashcards/{self.flashcard_id}", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @patch("src.db.supabase_client.get_supabase_client")
    def test_delete_flashcard_rate_limiting(self, mock_get_supabase):
        """Test that DELETE operations are rate limited."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock successful deletion
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        mock_delete_response = Mock()
        mock_delete_response.data = [self.sample_flashcard]

        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )
        mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_delete_response
        )

        # Act - Make multiple requests quickly (should trigger rate limit)
        successful_requests = 0
        rate_limited_requests = 0

        for i in range(55):  # Try more than the limit (50)
            response = self.client.delete(
                f"/api/v1/flashcards/{uuid.uuid4()}",  # Different UUID each time
                headers=self.auth_headers,
            )

            if response.status_code == status.HTTP_204_NO_CONTENT:
                successful_requests += 1
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited_requests += 1
                break  # Stop after first rate limit hit

        # Assert
        assert successful_requests > 0  # Some requests should succeed
        assert rate_limited_requests > 0  # Eventually should hit rate limit

        # Verify rate limit response has proper headers
        if rate_limited_requests > 0:
            rate_limit_response = self.client.delete(
                f"/api/v1/flashcards/{uuid.uuid4()}", headers=self.auth_headers
            )
            if rate_limit_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                assert "Retry-After" in rate_limit_response.headers

    @patch("src.db.supabase_client.get_supabase_client")
    def test_delete_flashcard_security_headers(self, mock_get_supabase):
        """Test that security headers are present in DELETE response."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock successful deletion
        mock_get_response = Mock()
        mock_get_response.data = [self.sample_flashcard]
        mock_delete_response = Mock()
        mock_delete_response.data = [self.sample_flashcard]

        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = (
            mock_get_response
        )
        mock_table.delete.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_delete_response
        )

        # Act
        response = self.client.delete(
            f"/api/v1/flashcards/{self.flashcard_id}", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Check security headers are present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
