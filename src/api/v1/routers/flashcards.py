import logging
import time
import uuid
from typing import Annotated, Any, Dict, Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.v1.routers.ai_router import get_authenticated_supabase_client
from src.api.v1.schemas.flashcard_schemas import (
    FlashcardManualCreateRequest,
    FlashcardPatchRequest,
    FlashcardResponse,
    FlashcardSourceEnum,
    FlashcardStatusEnum,
    ListFlashcardsQueryParams,
    PaginatedFlashcardsResponse,
)
from src.db.supabase_client import get_supabase_client
from src.services.flashcard_service import FlashcardService
from supabase import Client

logger = logging.getLogger(__name__)
security = HTTPBearer()


# Custom exception classes for better error handling
class FlashcardNotFoundError(Exception):
    """Raised when a flashcard is not found or not accessible."""

    def __init__(self, flashcard_id: uuid.UUID, user_id: uuid.UUID):
        self.flashcard_id = flashcard_id
        self.user_id = user_id
        super().__init__(f"Flashcard {flashcard_id} not found for user {user_id}")


class FlashcardServiceError(Exception):
    """Raised when flashcard service operations fail."""

    def __init__(self, operation: str, details: str):
        self.operation = operation
        self.details = details
        super().__init__(f"Flashcard service error during {operation}: {details}")


# Import utility functions from shared utils module
from src.api.v1.routers.utils import (
    add_security_headers,
    check_rate_limit,
    log_with_context,
    validate_request_integrity,
)

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> uuid.UUID:
    """
    Extract and validate user_id from JWT token.

    Args:
        credentials: JWT token from Authorization header
        supabase: Supabase client instance

    Returns:
        User UUID from validated token

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Get user from Supabase using the JWT token
        user_response = supabase.auth.get_user(credentials.credentials)

        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return uuid.UUID(user_response.user.id)

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_flashcard_service(
    request: Request,
    supabase: Annotated[Client, Depends(get_authenticated_supabase_client)],
) -> FlashcardService:
    """Dependency to get FlashcardService instance with authenticated client."""
    return FlashcardService(supabase)


def validate_flashcard_uuid(flashcard_id: uuid.UUID) -> uuid.UUID:
    """
    Custom validator for flashcard UUID.

    Args:
        flashcard_id: UUID to validate

    Returns:
        Validated UUID

    Raises:
        HTTPException: If UUID is invalid or represents an empty/null value
    """
    # Check if UUID is nil/empty (all zeros)
    if flashcard_id == uuid.UUID("00000000-0000-0000-0000-000000000000"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid flashcard ID. Empty UUID is not allowed.",
        )

    # Additional business validation can be added here
    # For example, check UUID version, validate specific patterns, etc.

    return flashcard_id


@router.get(
    "",
    response_model=PaginatedFlashcardsResponse,
    status_code=status.HTTP_200_OK,
    summary="List user's flashcards",
    description="Retrieve a paginated list of flashcards for the authenticated user. "
    "Supports filtering by status and source, with configurable pagination.",
)
async def list_user_flashcards(
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    flashcard_service: Annotated[FlashcardService, Depends(get_flashcard_service)],
    status_filter: Optional[FlashcardStatusEnum] = Query(
        default=FlashcardStatusEnum.ACTIVE,
        alias="status",
        description="Filter by flashcard status",
    ),
    source_filter: Optional[FlashcardSourceEnum] = Query(
        default=None, alias="source", description="Filter by flashcard source"
    ),
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    size: int = Query(default=20, ge=1, le=100, description="Number of items per page"),
) -> PaginatedFlashcardsResponse:
    """
    List user's flashcards with optional filtering and pagination.

    Args:
        status_filter: Filter flashcards by status (default: active)
        source_filter: Filter flashcards by source (optional)
        page: Page number for pagination (default: 1, min: 1)
        size: Number of items per page (default: 20, min: 1, max: 100)
        current_user_id: Authenticated user ID from JWT
        flashcard_service: Service for flashcard operations

    Returns:
        Paginated list of flashcards with metadata

    Raises:
        HTTPException: For various error conditions (401, 422, 500)
    """
    try:
        # Create query parameters object
        query_params = ListFlashcardsQueryParams(
            status=status_filter, source=source_filter, page=page, size=size
        )

        # Get flashcards using service
        result = flashcard_service.get_flashcards_for_user(
            user_id=current_user_id, params=query_params
        )

        return result

    except Exception as e:
        logger.error(f"Error listing flashcards for user {current_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving flashcards",
        )


@router.post(
    "",
    response_model=FlashcardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manual flashcard",
    description="Create a new flashcard manually with front and back content. "
    "The flashcard will be automatically marked as 'manual' source and 'active' status. "
    "A spaced repetition record will also be initialized for the flashcard.",
)
async def create_manual_flashcard(
    data: FlashcardManualCreateRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    flashcard_service: Annotated[FlashcardService, Depends(get_flashcard_service)],
) -> FlashcardResponse:
    """
    Create a manual flashcard.

    Args:
        data: Flashcard creation data (front_content, back_content)
        current_user_id: Authenticated user ID from JWT
        flashcard_service: Service for flashcard operations

    Returns:
        Created flashcard data

    Raises:
        HTTPException: For various error conditions (401, 422, 500)
    """
    try:
        # Create flashcard using service
        created_flashcard = flashcard_service.create_manual_flashcard(
            user_id=current_user_id, data=data
        )

        # Convert to response model
        return FlashcardResponse(**created_flashcard)

    except Exception as e:
        logger.error(f"Error creating flashcard for user {current_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while creating flashcard",
        )


@router.get(
    "/{flashcard_id}",
    response_model=FlashcardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific flashcard",
    description="Retrieve a specific flashcard by its UUID. "
    "Only the authenticated user can access their own flashcards due to Row Level Security.",
)
async def get_flashcard(
    request: Request,
    response: Response,
    flashcard_id: Annotated[
        uuid.UUID,
        Path(
            description="UUID of the flashcard to retrieve",
            example="550e8400-e29b-41d4-a716-446655440000",
        ),
    ],
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    flashcard_service: Annotated[FlashcardService, Depends(get_flashcard_service)],
) -> FlashcardResponse:
    """
    Get a specific flashcard by ID with enhanced security.

    Args:
        request: FastAPI Request object for security analysis
        response: FastAPI Response object for security headers
        flashcard_id: UUID of the flashcard to retrieve (validated)
        current_user_id: Authenticated user ID from JWT
        flashcard_service: Service for flashcard operations

    Returns:
        Flashcard data if found and accessible

    Raises:
        HTTPException: For various error conditions (400, 401, 404, 429, 500)
    """
    operation = "get_flashcard"
    start_time = time.time()

    try:
        # Add security headers
        add_security_headers(response)

        # Rate limiting check
        check_rate_limit(request, current_user_id, limit=100, window_minutes=60)

        # Request integrity validation
        validate_request_integrity(request, current_user_id)

        # Log request start with security context
        log_with_context(
            level="info",
            message="Starting secure flashcard retrieval",
            user_id=current_user_id,
            flashcard_id=flashcard_id,
            operation=operation,
            extra_context={
                "client_ip": getattr(request.client, "host", "unknown"),
                "user_agent": request.headers.get("user-agent", "unknown")[
                    :100
                ],  # Truncate for security
            },
        )

        # Enhanced input validation with custom validator
        try:
            validated_flashcard_id = validate_flashcard_uuid(flashcard_id)
        except HTTPException as e:
            log_with_context(
                level="warning",
                message="Invalid flashcard UUID provided",
                user_id=current_user_id,
                flashcard_id=flashcard_id,
                operation=operation,
                extra_context={"error": e.detail},
            )
            raise

        # Early return for obvious invalid cases
        if not current_user_id:
            log_with_context(
                level="warning",
                message="Unauthenticated request",
                flashcard_id=flashcard_id,
                operation=operation,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required",
            )

        # Get flashcard using service with enhanced security
        flashcard_data = flashcard_service.get_flashcard_by_id(
            flashcard_id=validated_flashcard_id, user_id=current_user_id
        )

        # Handle case where flashcard is not found or not accessible
        if flashcard_data is None:
            raise FlashcardNotFoundError(validated_flashcard_id, current_user_id)

        # Log successful retrieval with performance metrics
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="info",
            message="Successfully retrieved flashcard",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
            extra_context={"response_time_ms": round(elapsed_time, 2)},
        )

        # Convert to response model and return
        return FlashcardResponse(**flashcard_data)

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except FlashcardNotFoundError as e:
        log_with_context(
            level="info",
            message="Flashcard not found or not accessible",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found or you don't have access to it.",
        )
    except ValueError as e:
        log_with_context(
            level="error",
            message="Input validation error",
            user_id=current_user_id,
            flashcard_id=flashcard_id,
            operation=operation,
            extra_context={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request parameters"
        )
    except Exception as e:
        # Handle unexpected errors with detailed logging
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="error",
            message="Unexpected error during flashcard retrieval",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
            extra_context={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "response_time_ms": round(elapsed_time, 2),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving flashcard",
        )


@router.patch(
    "/{flashcard_id}",
    response_model=FlashcardResponse,
    status_code=status.HTTP_200_OK,
    summary="Update flashcard",
    description="Update a flashcard's content (front/back) or status (for AI-suggested cards). "
    "Supports partial updates - provide only the fields you want to change. "
    "Only the authenticated user can update their own flashcards.",
)
async def update_flashcard(
    request: Request,
    response: Response,
    flashcard_id: Annotated[
        uuid.UUID,
        Path(
            description="UUID of the flashcard to update",
            example="550e8400-e29b-41d4-a716-446655440000",
        ),
    ],
    patch_data: FlashcardPatchRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    flashcard_service: Annotated[FlashcardService, Depends(get_flashcard_service)],
) -> FlashcardResponse:
    """
    Update a flashcard with enhanced security and validation.

    Args:
        request: FastAPI Request object for security analysis
        response: FastAPI Response object for security headers
        flashcard_id: UUID of the flashcard to update (validated)
        patch_data: Fields to update (all optional)
        current_user_id: Authenticated user ID from JWT
        flashcard_service: Service for flashcard operations

    Returns:
        Updated flashcard data

    Raises:
        HTTPException: For various error conditions (400, 401, 404, 422, 429, 500)
    """
    operation = "update_flashcard"
    start_time = time.time()

    try:
        # Add security headers
        add_security_headers(response)

        # Rate limiting check
        check_rate_limit(request, current_user_id, limit=50, window_minutes=60)

        # Request integrity validation
        validate_request_integrity(request, current_user_id)

        # Log request start with security context
        log_with_context(
            level="info",
            message="Starting secure flashcard update",
            user_id=current_user_id,
            flashcard_id=flashcard_id,
            operation=operation,
            extra_context={
                "client_ip": getattr(request.client, "host", "unknown"),
                "user_agent": request.headers.get("user-agent", "unknown")[:100],
                "update_fields": [
                    field
                    for field, value in patch_data.model_dump(
                        exclude_unset=True
                    ).items()
                    if value is not None
                ],
            },
        )

        # Enhanced input validation with custom validator
        try:
            validated_flashcard_id = validate_flashcard_uuid(flashcard_id)
        except HTTPException as e:
            log_with_context(
                level="warning",
                message="Invalid flashcard UUID provided for update",
                user_id=current_user_id,
                flashcard_id=flashcard_id,
                operation=operation,
                extra_context={"error": e.detail},
            )
            raise

        # Early return for obvious invalid cases
        if not current_user_id:
            log_with_context(
                level="warning",
                message="Unauthenticated update request",
                flashcard_id=flashcard_id,
                operation=operation,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required",
            )

        # Convert patch data to dict, excluding unset/None fields
        updates = patch_data.model_dump(exclude_unset=True, exclude_none=True)

        # Check if any updates provided
        if not updates:
            log_with_context(
                level="warning",
                message="Empty update request",
                user_id=current_user_id,
                flashcard_id=validated_flashcard_id,
                operation=operation,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update",
            )

        # Update flashcard using service with enhanced security
        updated_flashcard = flashcard_service.update_flashcard(
            flashcard_id=validated_flashcard_id,
            user_id=current_user_id,
            updates=updates,
        )

        # Handle case where flashcard is not found or not accessible
        if updated_flashcard is None:
            raise FlashcardNotFoundError(validated_flashcard_id, current_user_id)

        # Log successful update with performance metrics
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="info",
            message="Successfully updated flashcard",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
            extra_context={
                "response_time_ms": round(elapsed_time, 2),
                "updated_fields": list(updates.keys()),
            },
        )

        # Convert to response model and return
        return FlashcardResponse(**updated_flashcard)

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except FlashcardNotFoundError as e:
        log_with_context(
            level="info",
            message="Flashcard not found or not accessible for update",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found or you don't have access to it.",
        )
    except ValueError as e:
        log_with_context(
            level="warning",
            message="Validation error during flashcard update",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
            extra_context={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors with detailed logging
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="error",
            message="Unexpected error during flashcard update",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
            extra_context={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "response_time_ms": round(elapsed_time, 2),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while updating flashcard",
        )


@router.delete(
    "/{flashcard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete flashcard",
    description="Delete a specific flashcard permanently. This operation is irreversible and will "
    "also remove all associated spaced repetition data. Only the authenticated user "
    "can delete their own flashcards due to Row Level Security policies.",
)
async def delete_flashcard(
    request: Request,
    response: Response,
    flashcard_id: Annotated[
        uuid.UUID,
        Path(
            description="UUID of the flashcard to delete",
            example="550e8400-e29b-41d4-a716-446655440000",
        ),
    ],
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    flashcard_service: Annotated[FlashcardService, Depends(get_flashcard_service)],
) -> None:
    """
    Delete a specific flashcard by ID with enhanced security.

    Args:
        request: FastAPI Request object for security analysis
        response: FastAPI Response object for security headers
        flashcard_id: UUID of the flashcard to delete (validated)
        current_user_id: Authenticated user ID from JWT
        flashcard_service: Service for flashcard operations

    Returns:
        Empty response with 204 No Content status

    Raises:
        HTTPException: For various error conditions (400, 401, 404, 422, 429, 500)
    """
    operation = "delete_flashcard"
    start_time = time.time()

    try:
        # Add security headers
        add_security_headers(response)

        # Rate limiting check (stricter for DELETE operations)
        check_rate_limit(request, current_user_id, limit=50, window_minutes=60)

        # Request integrity validation
        validate_request_integrity(request, current_user_id)

        # Log request start with security context
        log_with_context(
            level="info",
            message="Starting secure flashcard deletion",
            user_id=current_user_id,
            flashcard_id=flashcard_id,
            operation=operation,
            extra_context={
                "client_ip": getattr(request.client, "host", "unknown"),
                "user_agent": request.headers.get("user-agent", "unknown")[
                    :100
                ],  # Truncate for security
            },
        )

        # Enhanced input validation with custom validator
        try:
            validated_flashcard_id = validate_flashcard_uuid(flashcard_id)
        except HTTPException as e:
            log_with_context(
                level="warning",
                message="Invalid flashcard UUID provided for deletion",
                user_id=current_user_id,
                flashcard_id=flashcard_id,
                operation=operation,
                extra_context={"error": e.detail},
            )
            raise

        # Early return for obvious invalid cases
        if not current_user_id:
            log_with_context(
                level="warning",
                message="Unauthenticated deletion request",
                flashcard_id=flashcard_id,
                operation=operation,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required",
            )

        # Delete flashcard using service with enhanced security
        deletion_successful = flashcard_service.delete_flashcard_by_id(
            flashcard_id=validated_flashcard_id, user_id=current_user_id
        )

        # Handle case where flashcard was not found or not accessible
        if not deletion_successful:
            raise FlashcardNotFoundError(validated_flashcard_id, current_user_id)

        # Log successful deletion with performance metrics
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="info",
            message="Successfully deleted flashcard",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
            extra_context={"response_time_ms": round(elapsed_time, 2)},
        )

        # Return 204 No Content (empty response)
        return None

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except FlashcardNotFoundError as e:
        log_with_context(
            level="info",
            message="Flashcard not found or not accessible for deletion",
            user_id=current_user_id,
            flashcard_id=validated_flashcard_id,
            operation=operation,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found or you don't have access to it.",
        )
    except ValueError as e:
        log_with_context(
            level="warning",
            message="Validation error during flashcard deletion",
            user_id=current_user_id,
            flashcard_id=flashcard_id,
            operation=operation,
            extra_context={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}",
        )
    except FlashcardServiceError as e:
        log_with_context(
            level="error",
            message="Service error during flashcard deletion",
            user_id=current_user_id,
            flashcard_id=flashcard_id,
            operation=operation,
            extra_context={"error": e.details},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service error occurred while deleting flashcard",
        )
    except Exception as e:
        log_with_context(
            level="error",
            message="Unexpected error during flashcard deletion",
            user_id=current_user_id,
            flashcard_id=flashcard_id,
            operation=operation,
            extra_context={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while deleting flashcard",
        )
