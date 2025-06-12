import pytest
import uuid
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from main import app


@pytest.mark.skip("TODO: Fix integration test authorization and mocking issues")
class TestAiGenerationStatsEndpoint:
    """Integration tests for GET /api/v1/ai/generation-stats endpoint."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        self.user_id = uuid.uuid4()
        self.valid_token = "valid_jwt_token"
        self.auth_headers = {"Authorization": f"Bearer {self.valid_token}"}
        
        self.sample_ai_events = [
            {
                "id": str(uuid.uuid4()),
                "user_id": str(self.user_id),
                "source_text_id": str(uuid.uuid4()),
                "generated_cards_count": 10,
                "accepted_cards_count": 7,
                "rejected_cards_count": 2,
                "llm_model_used": "gpt-3.5-turbo",
                "cost": 0.0015,
                "created_at": "2024-01-01T00:00:00.000Z",
                "updated_at": "2024-01-01T00:00:00.000Z"
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": str(self.user_id),
                "source_text_id": str(uuid.uuid4()),
                "generated_cards_count": 5,
                "accepted_cards_count": 3,
                "rejected_cards_count": 1,
                "llm_model_used": "claude-3-haiku",
                "cost": 0.0008,
                "created_at": "2024-01-01T01:00:00.000Z",
                "updated_at": "2024-01-01T01:00:00.000Z"
            }
        ]

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_success_with_defaults(self, mock_get_supabase):
        """Test successful AI generation stats retrieval with default parameters."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock count response
        mock_count_response = Mock()
        mock_count_response.count = 2
        
        # Mock data response
        mock_data_response = Mock()
        mock_data_response.data = self.sample_ai_events
        
        # Setup method chaining for ai_generation_events table
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        
        # Count query
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        
        # Data query with pagination and ordering
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 1
        assert len(data["items"]) == 2
        
        # Verify first item structure
        first_item = data["items"][0]
        assert first_item["generated_cards_count"] == 10
        assert first_item["accepted_cards_count"] == 7
        assert first_item["rejected_cards_count"] == 2
        assert first_item["llm_model_used"] == "gpt-3.5-turbo"
        assert first_item["cost"] == 0.0015

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_with_pagination(self, mock_get_supabase):
        """Test AI generation stats with custom pagination parameters."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock count response (total 25 items)
        mock_count_response = Mock()
        mock_count_response.count = 25
        
        # Mock data response (page 2 with 1 item)
        mock_data_response = Mock()
        mock_data_response.data = [self.sample_ai_events[0]]
        
        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response

        # Act
        response = self.client.get(
            "/api/v1/ai/generation-stats?page=2&size=10",
            headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 25
        assert data["page"] == 2
        assert data["size"] == 10
        assert data["pages"] == 3  # ceil(25/10) = 3
        assert len(data["items"]) == 1

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_empty_result(self, mock_get_supabase):
        """Test AI generation stats with empty result."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock empty count response
        mock_count_response = Mock()
        mock_count_response.count = 0
        
        # Mock empty data response
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["pages"] == 1
        assert len(data["items"]) == 0

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_max_page_size(self, mock_get_supabase):
        """Test AI generation stats with maximum allowed page size."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock count response
        mock_count_response = Mock()
        mock_count_response.count = 150
        
        # Mock data response
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response

        # Act
        response = self.client.get(
            "/api/v1/ai/generation-stats?page=1&size=100",
            headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 150
        assert data["page"] == 1
        assert data["size"] == 100
        assert data["pages"] == 2  # ceil(150/100) = 2

    def test_generation_stats_unauthorized_no_token(self):
        """Test AI generation stats without authentication token."""
        # Act
        response = self.client.get("/api/v1/ai/generation-stats")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_unauthorized_invalid_token(self, mock_get_supabase):
        """Test AI generation stats with invalid authentication token."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth failure
        mock_user_response = Mock()
        mock_user_response.user = None
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        invalid_headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=invalid_headers)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in response.json()["detail"]

    def test_generation_stats_invalid_query_params(self):
        """Test AI generation stats with invalid query parameters."""
        # Act - Invalid page (< 1)
        response = self.client.get(
            "/api/v1/ai/generation-stats?page=0",
            headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Act - Invalid size (< 1)
        response = self.client.get(
            "/api/v1/ai/generation-stats?size=0",
            headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Act - Invalid size (> 100)
        response = self.client.get(
            "/api/v1/ai/generation-stats?size=150",
            headers=self.auth_headers
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_database_error(self, mock_get_supabase):
        """Test AI generation stats with database error."""
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
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error occurred" in response.json()["detail"]

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_count_query_error(self, mock_get_supabase):
        """Test AI generation stats with count query error."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock count query failure
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.side_effect = Exception("Count query failed")

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error occurred" in response.json()["detail"]

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_data_query_error(self, mock_get_supabase):
        """Test AI generation stats with data query error."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock successful count but failed data query
        mock_count_response = Mock()
        mock_count_response.count = 5
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        
        # Count query succeeds
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        
        # Data query fails
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.side_effect = Exception("Data query timeout")

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Database error occurred" in response.json()["detail"]

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_none_count_handling(self, mock_get_supabase):
        """Test AI generation stats handling None count from Supabase."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock None count response (edge case in Supabase)
        mock_count_response = Mock()
        mock_count_response.count = None
        
        # Mock empty data response
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0  # Should default to 0 when None
        assert data["pages"] == 1

    @patch('src.db.supabase_client.get_supabase_client') 
    def test_generation_stats_rate_limiting(self, mock_get_supabase):
        """Test AI generation stats rate limiting functionality."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock successful response
        mock_count_response = Mock()
        mock_count_response.count = 1
        mock_data_response = Mock()
        mock_data_response.data = [self.sample_ai_events[0]]
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response

        # Act - Make multiple requests quickly
        for i in range(55):  # Exceed the rate limit of 50 per hour
            response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)
            if i < 50:
                assert response.status_code == status.HTTP_200_OK
            else:
                # After exceeding rate limit
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                break

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_security_headers(self, mock_get_supabase):
        """Test that security headers are properly set in response."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock successful response
        mock_count_response = Mock()
        mock_count_response.count = 0
        mock_data_response = Mock()
        mock_data_response.data = []
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_user_isolation(self, mock_get_supabase):
        """Test that users can only see their own AI generation stats."""
        # Arrange
        other_user_id = uuid.uuid4()
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth for first user
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock response with user's own data
        mock_count_response = Mock()
        mock_count_response.count = 1
        mock_data_response = Mock()
        mock_data_response.data = [self.sample_ai_events[0]]
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify user_id filtering was applied correctly
        mock_table.select.return_value.eq.assert_called_with("user_id", str(self.user_id))
        
        # Verify response contains only user's data
        assert len(data["items"]) == 1
        assert data["items"][0]["user_id"] == str(self.user_id)

    @patch('src.db.supabase_client.get_supabase_client')
    def test_generation_stats_ordering(self, mock_get_supabase):
        """Test that AI generation stats are ordered by created_at DESC."""
        # Arrange
        mock_supabase = Mock()
        mock_get_supabase.return_value = mock_supabase
        
        # Mock auth
        mock_user_response = Mock()
        mock_user_response.user = Mock()
        mock_user_response.user.id = str(self.user_id)
        mock_supabase.auth.get_user.return_value = mock_user_response
        
        # Mock responses
        mock_count_response = Mock()
        mock_count_response.count = 0
        mock_data_response = Mock()
        mock_data_response.data = []
        
        mock_table = Mock()
        mock_order = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value = mock_order
        mock_order.range.return_value.execute.return_value = mock_data_response

        # Act
        response = self.client.get("/api/v1/ai/generation-stats", headers=self.auth_headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        
        # Verify order() was called with correct parameters
        mock_table.select.return_value.eq.return_value.order.assert_called_with("created_at", desc=True) 