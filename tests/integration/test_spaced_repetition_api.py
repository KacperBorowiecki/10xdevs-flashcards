import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import app


@pytest.mark.skip("TODO: Fix integration test authorization and mocking issues")
class TestSpacedRepetitionDueCardsEndpoint:
    """Integration tests for GET /api/v1/spaced-repetition/due-cards endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.user_id = uuid.uuid4()
        self.valid_token = "valid_jwt_token"
        self.auth_headers = {"Authorization": f"Bearer {self.valid_token}"}

        # Sample flashcards with spaced repetition data
        self.flashcard_1_id = uuid.uuid4()
        self.flashcard_2_id = uuid.uuid4()

        # Due flashcard (due yesterday)
        self.due_flashcard_1 = {
            "id": str(self.flashcard_1_id),
            "user_id": str(self.user_id),
            "source_text_id": None,
            "front_content": "What is Python?",
            "back_content": "A programming language",
            "source": "manual",
            "status": "active",
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-01T00:00:00.000Z",
            "user_flashcard_spaced_repetition": [
                {
                    "due_date": (datetime.utcnow() - timedelta(days=1)).isoformat()
                    + "Z",
                    "current_interval": 1,
                    "last_reviewed_at": None,
                }
            ],
        }

        # Due flashcard (due now)
        self.due_flashcard_2 = {
            "id": str(self.flashcard_2_id),
            "user_id": str(self.user_id),
            "source_text_id": str(uuid.uuid4()),
            "front_content": "What is FastAPI?",
            "back_content": "A modern web framework",
            "source": "ai_suggestion",
            "status": "active",
            "created_at": "2024-01-01T01:00:00.000Z",
            "updated_at": "2024-01-01T01:00:00.000Z",
            "user_flashcard_spaced_repetition": [
                {
                    "due_date": datetime.utcnow().isoformat() + "Z",
                    "current_interval": 3,
                    "last_reviewed_at": (
                        datetime.utcnow() - timedelta(days=3)
                    ).isoformat()
                    + "Z",
                }
            ],
        }

        # Not due flashcard (due tomorrow)
        self.not_due_flashcard = {
            "id": str(uuid.uuid4()),
            "user_id": str(self.user_id),
            "source_text_id": None,
            "front_content": "What is Django?",
            "back_content": "Another Python web framework",
            "source": "manual",
            "status": "active",
            "created_at": "2024-01-01T02:00:00.000Z",
            "updated_at": "2024-01-01T02:00:00.000Z",
            "user_flashcard_spaced_repetition": [
                {
                    "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
                    + "Z",
                    "current_interval": 2,
                    "last_reviewed_at": (
                        datetime.utcnow() - timedelta(days=1)
                    ).isoformat()
                    + "Z",
                }
            ],
        }

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_success(self, mock_get_supabase):
        """Test successful due flashcards retrieval."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database response
        mock_response = Mock()
        mock_response.data = [self.due_flashcard_1]

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["front_content"] == "What is Python?"
        assert "repetition_data" in data[0]

    def test_get_due_flashcards_unauthorized(self):
        """Test due flashcards retrieval without authentication."""
        # Act
        response = self.client.get("/api/v1/spaced-repetition/due-cards")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_due_flashcards_invalid_limit(self):
        """Test due flashcards retrieval with invalid limit."""
        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards?limit=0", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_success_with_defaults(self, mock_get_supabase):
        """Test successful due flashcards retrieval with default parameters."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database response - return all flashcards, filtering will be done in service
        mock_response = Mock()
        mock_response.data = [
            self.due_flashcard_1,
            self.due_flashcard_2,
            self.not_due_flashcard,
        ]

        # Setup method chaining for the complex query
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # Only due flashcards should be returned

        # Check first flashcard
        assert data[0]["id"] == str(self.flashcard_1_id)
        assert data[0]["front_content"] == "What is Python?"
        assert "repetition_data" in data[0]
        assert data[0]["repetition_data"]["current_interval"] == 1
        assert data[0]["repetition_data"]["last_reviewed_at"] is None

        # Check second flashcard
        assert data[1]["id"] == str(self.flashcard_2_id)
        assert data[1]["front_content"] == "What is FastAPI?"
        assert "repetition_data" in data[1]
        assert data[1]["repetition_data"]["current_interval"] == 3
        assert data[1]["repetition_data"]["last_reviewed_at"] is not None

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_with_limit(self, mock_get_supabase):
        """Test due flashcards retrieval with custom limit."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database response with multiple due cards
        mock_response = Mock()
        mock_response.data = [self.due_flashcard_1, self.due_flashcard_2]

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act - request only 1 card
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards?limit=1", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1  # Should return only 1 card due to limit
        assert data[0]["id"] == str(self.flashcard_1_id)  # Should be sorted by due_date

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_empty_result(self, mock_get_supabase):
        """Test due flashcards retrieval with no due cards."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock database response with no due cards
        mock_response = Mock()
        mock_response.data = [self.not_due_flashcard]  # Only not due card

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # No due cards

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_no_flashcards(self, mock_get_supabase):
        """Test due flashcards retrieval when user has no flashcards."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock empty database response
        mock_response = Mock()
        mock_response.data = None

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_unauthorized_invalid_token(self, mock_get_supabase):
        """Test due flashcards retrieval with invalid authentication token."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth failure
        mock_user_response = Mock()
        mock_user_response.user = None
        mock_supabase.auth.get_user.return_value = mock_user_response

        invalid_headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=invalid_headers
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in response.json()["detail"]

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_database_error(self, mock_get_supabase):
        """Test due flashcards retrieval with database error."""
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
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal server error" in response.json()["detail"]

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_service_validation_error(self, mock_get_supabase):
        """Test due flashcards retrieval with service validation error."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth with invalid user ID (nil UUID)
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = "00000000-0000-0000-0000-000000000000"  # Nil UUID
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid request parameters" in response.json()["detail"]

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_malformed_date_handling(self, mock_get_supabase):
        """Test due flashcards retrieval with malformed date data."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock flashcard with malformed date
        malformed_flashcard = {
            "id": str(uuid.uuid4()),
            "user_id": str(self.user_id),
            "source_text_id": None,
            "front_content": "Test card",
            "back_content": "Test answer",
            "source": "manual",
            "status": "active",
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-01T00:00:00.000Z",
            "user_flashcard_spaced_repetition": [
                {
                    "due_date": "invalid-date-format",
                    "current_interval": 1,
                    "last_reviewed_at": None,
                }
            ],
        }

        mock_response = Mock()
        mock_response.data = [malformed_flashcard]

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Malformed card should be filtered out

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_missing_spaced_repetition_data(self, mock_get_supabase):
        """Test due flashcards retrieval with missing spaced repetition data."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock flashcard without spaced repetition data
        flashcard_without_sr = {
            "id": str(uuid.uuid4()),
            "user_id": str(self.user_id),
            "source_text_id": None,
            "front_content": "Test card",
            "back_content": "Test answer",
            "source": "manual",
            "status": "active",
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-01T00:00:00.000Z",
            "user_flashcard_spaced_repetition": [],  # Empty array
        }

        mock_response = Mock()
        mock_response.data = [flashcard_without_sr]

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # Card without SR data should be filtered out

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_sorting_by_due_date(self, mock_get_supabase):
        """Test that due flashcards are sorted by due_date (earliest first)."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Create flashcards with different due dates
        older_due_card = self.due_flashcard_1.copy()
        older_due_card["user_flashcard_spaced_repetition"][0]["due_date"] = (
            datetime.utcnow() - timedelta(days=2)
        ).isoformat() + "Z"

        newer_due_card = self.due_flashcard_2.copy()
        newer_due_card["user_flashcard_spaced_repetition"][0]["due_date"] = (
            datetime.utcnow() - timedelta(hours=1)
        ).isoformat() + "Z"

        # Return cards in reverse chronological order
        mock_response = Mock()
        mock_response.data = [newer_due_card, older_due_card]

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

        # First card should be the one due earlier (older_due_card)
        assert data[0]["id"] == str(self.flashcard_1_id)
        # Second card should be the one due later (newer_due_card)
        assert data[1]["id"] == str(self.flashcard_2_id)

    @patch("src.db.supabase_client.get_supabase_client")
    def test_get_due_flashcards_security_headers(self, mock_get_supabase):
        """Test that security headers are added to the response."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase

        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response

        # Mock empty response
        mock_response = Mock()
        mock_response.data = []

        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        # Act
        response = self.client.get(
            "/api/v1/spaced-repetition/due-cards", headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Check security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert (
            response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        )
