import pytest
import uuid
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.services.ai_generation_service import AiGenerationService, AiGenerationServiceError
from src.api.v1.schemas.ai_schemas import PaginatedAiGenerationStatsResponse
from src.db.schemas import AiGenerationEvent


class TestAiGenerationServiceGetUserGenerationStats:
    """Test suite for AiGenerationService.get_user_generation_stats method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_supabase = Mock()
        self.service = AiGenerationService(self.mock_supabase)
        self.user_id = uuid.uuid4()
        self.sample_events = [
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

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_default_params(self):
        """Test getting AI generation stats with default parameters."""
        # Arrange
        page, size = 1, 20
        
        # Mock count response
        mock_count_response = Mock()
        mock_count_response.count = 2
        
        # Mock data response  
        mock_data_response = Mock()
        mock_data_response.data = self.sample_events
        
        # Setup method chaining for count query
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        
        # First call: count query
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        
        # Second call: data query
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act
        result = await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert
        assert isinstance(result, PaginatedAiGenerationStatsResponse)
        assert result.total == 2
        assert result.page == 1
        assert result.size == 20
        assert result.pages == 1
        assert len(result.items) == 2
        assert result.items[0].generated_cards_count == 10
        assert result.items[1].generated_cards_count == 5

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_pagination(self):
        """Test AI generation stats with pagination."""
        # Arrange
        page, size = 2, 5
        
        mock_count_response = Mock()
        mock_count_response.count = 12  # Total of 12 events
        
        mock_data_response = Mock()
        mock_data_response.data = []  # Empty page 2 result
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act
        result = await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert
        assert result.total == 12
        assert result.page == 2
        assert result.size == 5
        assert result.pages == 3  # ceil(12/5) = 3
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_empty_result(self):
        """Test handling empty AI generation stats result."""
        # Arrange
        page, size = 1, 20
        
        mock_count_response = Mock()
        mock_count_response.count = 0
        
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act
        result = await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert
        assert result.total == 0
        assert result.page == 1
        assert result.size == 20
        assert result.pages == 1
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_with_none_count(self):
        """Test handling None count from Supabase."""
        # Arrange
        page, size = 1, 20
        
        mock_count_response = Mock()
        mock_count_response.count = None  # Supabase sometimes returns None
        
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act
        result = await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert
        assert result.total == 0  # Should default to 0 when None
        assert result.pages == 1

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_range_calculation(self):
        """Test correct range calculation for Supabase pagination."""
        # Arrange
        page, size = 3, 10
        expected_offset = (page - 1) * size  # 20
        expected_end = expected_offset + size - 1  # 29
        
        mock_count_response = Mock()
        mock_count_response.count = 50
        
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining with verification
        mock_table = Mock()
        mock_range = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value = mock_range
        mock_range.execute.return_value = mock_data_response
        
        # Act
        await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert - verify range() was called with correct parameters
        mock_table.select.return_value.eq.return_value.order.return_value.range.assert_called_with(
            expected_offset, expected_end
        )

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_user_id_conversion(self):
        """Test that user_id is properly converted to string for Supabase."""
        # Arrange
        page, size = 1, 20
        
        mock_count_response = Mock()
        mock_count_response.count = 0
        
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining with verification
        mock_table = Mock()
        mock_eq = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value = mock_eq
        mock_eq.execute.return_value = mock_count_response
        mock_eq.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act
        await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert - verify eq() was called with string version of user_id
        mock_table.select.return_value.eq.assert_called_with("user_id", str(self.user_id))

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_model_conversion(self):
        """Test proper conversion of database records to Pydantic models."""
        # Arrange
        page, size = 1, 20
        
        mock_count_response = Mock()
        mock_count_response.count = 1
        
        mock_data_response = Mock()
        mock_data_response.data = [self.sample_events[0]]
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act
        result = await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert
        assert len(result.items) == 1
        event = result.items[0]
        assert isinstance(event, AiGenerationEvent)
        assert str(event.id) == self.sample_events[0]["id"]
        assert str(event.user_id) == self.sample_events[0]["user_id"]
        assert event.generated_cards_count == 10
        assert event.llm_model_used == "gpt-3.5-turbo"
        assert event.cost == 0.0015

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_count_query_error(self):
        """Test handling count query database error."""
        # Arrange
        page, size = 1, 20
        
        # Mock database error on count query
        self.mock_supabase.table.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(AiGenerationServiceError) as exc_info:
            await self.service.get_user_generation_stats(self.user_id, page, size)
        
        assert exc_info.value.operation == "get_user_generation_stats"
        assert "Database query failed" in exc_info.value.details
        assert "Database connection error" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_data_query_error(self):
        """Test handling data query database error."""
        # Arrange
        page, size = 1, 20
        
        # Mock successful count but failed data query
        mock_count_response = Mock()
        mock_count_response.count = 5
        
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        
        # Count query succeeds
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        
        # Data query fails
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.side_effect = Exception("Query timeout")
        
        # Act & Assert
        with pytest.raises(AiGenerationServiceError) as exc_info:
            await self.service.get_user_generation_stats(self.user_id, page, size)
        
        assert exc_info.value.operation == "get_user_generation_stats"
        assert "Database query failed" in exc_info.value.details
        assert "Query timeout" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_model_validation_error(self):
        """Test handling Pydantic model validation errors."""
        # Arrange
        page, size = 1, 20
        
        # Invalid data that will cause Pydantic validation to fail
        invalid_event = {
            "id": "invalid-uuid",  # Invalid UUID format
            "user_id": str(self.user_id),
            "source_text_id": str(uuid.uuid4()),
            "generated_cards_count": "not-a-number",  # Invalid type
            "accepted_cards_count": 7,
            "rejected_cards_count": 2,
            "llm_model_used": "gpt-3.5-turbo",
            "cost": 0.0015,
            "created_at": "2024-01-01T00:00:00.000Z",
            "updated_at": "2024-01-01T00:00:00.000Z"
        }
        
        mock_count_response = Mock()
        mock_count_response.count = 1
        
        mock_data_response = Mock()
        mock_data_response.data = [invalid_event]
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act & Assert
        with pytest.raises(AiGenerationServiceError) as exc_info:
            await self.service.get_user_generation_stats(self.user_id, page, size)
        
        assert exc_info.value.operation == "get_user_generation_stats"
        assert "Database query failed" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_edge_case_zero_size(self):
        """Test edge case where size calculation results in zero pages."""
        # Arrange
        page, size = 1, 20
        
        mock_count_response = Mock()
        mock_count_response.count = 0
        
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act
        result = await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert - should default to 1 page even with 0 total
        assert result.pages == 1

    @pytest.mark.asyncio
    async def test_get_user_generation_stats_verify_table_calls(self):
        """Test that correct table and query methods are called."""
        # Arrange
        page, size = 1, 20
        
        mock_count_response = Mock()
        mock_count_response.count = 0
        
        mock_data_response = Mock()
        mock_data_response.data = []
        
        # Setup method chaining
        mock_table = Mock()
        self.mock_supabase.table.return_value = mock_table
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_count_response
        mock_table.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_data_response
        
        # Act
        await self.service.get_user_generation_stats(self.user_id, page, size)
        
        # Assert
        # Verify table() was called with correct table name
        self.mock_supabase.table.assert_called_with("ai_generation_events")
        
        # Verify order() was called with correct parameters for data query
        mock_table.select.return_value.eq.return_value.order.assert_called_with("created_at", desc=True)


class TestAiGenerationServiceInitialization:
    """Test suite for AiGenerationService initialization."""

    def test_service_initialization(self):
        """Test proper service initialization."""
        # Arrange
        mock_supabase = Mock()
        
        # Act
        service = AiGenerationService(mock_supabase)
        
        # Assert
        assert service.supabase == mock_supabase

    def test_dependency_factory(self):
        """Test get_ai_generation_service dependency factory."""
        # Arrange
        from src.services.ai_generation_service import get_ai_generation_service
        mock_supabase = Mock()
        
        # Act
        service = get_ai_generation_service(mock_supabase)
        
        # Assert
        assert isinstance(service, AiGenerationService)
        assert service.supabase == mock_supabase


class TestAiGenerationServiceError:
    """Test suite for AiGenerationServiceError exception."""

    def test_error_creation(self):
        """Test AiGenerationServiceError creation with operation and details."""
        # Arrange
        operation = "test_operation"
        details = "Test error details"
        
        # Act
        error = AiGenerationServiceError(operation, details)
        
        # Assert
        assert error.operation == operation
        assert error.details == details
        assert operation in str(error)
        assert details in str(error)

    def test_error_inheritance(self):
        """Test that AiGenerationServiceError inherits from Exception."""
        # Arrange & Act
        error = AiGenerationServiceError("test", "test")
        
        # Assert
        assert isinstance(error, Exception)
        
        # Test that it can be raised and caught
        with pytest.raises(AiGenerationServiceError):
            raise error 