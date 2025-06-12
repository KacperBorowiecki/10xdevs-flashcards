import logging
import time
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from src.api.v1.schemas.ai_schemas import PaginatedAiGenerationStatsResponse
from src.core.config import settings
from src.db.supabase_client import get_supabase_client
from src.dtos import AIGenerateFlashcardsRequest, AIGenerateFlashcardsResponse
from src.middleware.auth_middleware import get_current_user
from src.services.ai_generation_service import (
    AiGenerationService,
    AiGenerationServiceError,
    get_ai_generation_service,
)
from src.services.ai_service import AIService, AIServiceError, get_ai_service
from src.services.auth_service import AuthService
from src.services.llm_client import LLMServiceError
from supabase import Client, ClientOptions, create_client

logger = logging.getLogger(__name__)

# Import utility functions from shared utils module
from src.api.v1.routers.utils import (
    add_security_headers,
    check_rate_limit,
    log_with_context,
    validate_request_integrity,
)

router = APIRouter(prefix="/ai", tags=["ai"])


async def require_auth_for_ai(
    request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> uuid.UUID:
    """
    Dependency that requires authentication for AI endpoints and returns user UUID.
    Uses session-based authentication consistent with other parts of the application.

    Args:
        request: FastAPI request object
        current_user: Current user data from middleware

    Returns:
        User UUID from authenticated session

    Raises:
        HTTPException: If user is not authenticated
    """
    if not current_user:
        # Check if user is authenticated via cookie (fallback)
        if not AuthService.is_authenticated(request):
            logger.info("Unauthenticated API request for AI services")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # Get user data from auth cookie (fallback)
        auth_data = AuthService.get_auth_data(request)
        if not auth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        user_id_str = auth_data.get("user_id")
    else:
        user_id_str = current_user.get("id")

    if not user_id_str:
        logger.error("User ID not found in authentication data")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data",
        )

    try:
        return uuid.UUID(str(user_id_str))
    except ValueError:
        logger.error(f"Invalid user ID format: {user_id_str}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID format"
        )


def get_authenticated_supabase_client(request: Request) -> Client:
    """
    Create Supabase client with user authentication token for RLS.

    Args:
        request: FastAPI request object to extract auth token from cookies

    Returns:
        Authenticated Supabase client

    Raises:
        HTTPException: If no auth token is found
    """
    # Get access token from cookies
    access_token = request.cookies.get("access_token")

    if not access_token:
        logger.error("No access token found in cookies for RLS operations")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required for database operations",
        )

    # Create authenticated Supabase client with user token
    try:
        client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_anon_key,
            options=ClientOptions(headers={"Authorization": f"Bearer {access_token}"}),
        )
        logger.debug(f"Created authenticated Supabase client for user")
        return client
    except Exception as e:
        logger.error(f"Failed to create authenticated Supabase client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize database connection",
        )


def get_ai_service_dependency(
    supabase: Annotated[Client, Depends(get_authenticated_supabase_client)],
) -> AIService:
    """Dependency to get AIService instance with authenticated client."""
    return get_ai_service(supabase)


def get_ai_generation_service_dependency(
    supabase: Annotated[Client, Depends(get_authenticated_supabase_client)],
) -> AiGenerationService:
    """Dependency to get AiGenerationService instance with authenticated client."""
    return get_ai_generation_service(supabase)


@router.post(
    "/generate-flashcards",
    response_model=AIGenerateFlashcardsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate flashcards from text using AI",
    description="Generate educational flashcards from provided text (1000-10000 characters) using AI. "
    "The service creates source text, generates flashcard suggestions with pending_review status, "
    "and tracks the generation event for analytics. Users can later review and approve/reject suggestions.",
)
async def generate_flashcards(
    request: Request,
    response: Response,
    data: AIGenerateFlashcardsRequest,
    current_user_id: Annotated[uuid.UUID, Depends(require_auth_for_ai)],
    ai_service: Annotated[AIService, Depends(get_ai_service_dependency)],
) -> AIGenerateFlashcardsResponse:
    """
    Generate flashcards from text using AI with enhanced security and monitoring.

    Args:
        request: FastAPI Request object for security analysis
        response: FastAPI Response object for security headers
        data: Request data with text_content (1000-10000 characters)
        current_user_id: Authenticated user ID from JWT
        ai_service: AI service for flashcard generation

    Returns:
        Response with generated flashcard suggestions and metadata

    Raises:
        HTTPException: For various error conditions (400, 401, 422, 503, 500)
    """
    operation = "ai_generate_flashcards"
    start_time = time.time()

    try:
        # Add security headers
        add_security_headers(response)

        # Rate limiting check (more restrictive for AI operations)
        check_rate_limit(request, current_user_id, limit=10, window_minutes=60)

        # Request integrity validation
        validate_request_integrity(request, current_user_id)

        # Log request start with security context
        log_with_context(
            level="info",
            message="Starting AI flashcard generation",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "client_ip": getattr(request.client, "host", "unknown"),
                "user_agent": request.headers.get("user-agent", "unknown")[:100],
                "text_length": len(data.text_content),
                "text_preview": (
                    data.text_content[:100] + "..."
                    if len(data.text_content) > 100
                    else data.text_content
                ),
            },
        )

        # Early return for obvious invalid cases
        if not current_user_id:
            log_with_context(
                level="warning",
                message="Unauthenticated AI generation request",
                operation=operation,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required",
            )

        # Additional validation for AI requests
        if len(data.text_content.strip()) == 0:
            log_with_context(
                level="warning",
                message="Empty text content provided",
                user_id=current_user_id,
                operation=operation,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content cannot be empty",
            )

        # Generate flashcards using AI service
        result = await ai_service.generate_flashcards_from_text(
            request=data, user_id=current_user_id
        )

        # Log successful generation with performance metrics
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="info",
            message="Successfully generated AI flashcards",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "source_text_id": str(result.source_text_id),
                "ai_event_id": str(result.ai_generation_event_id),
                "flashcards_count": len(result.suggested_flashcards),
                "response_time_ms": round(elapsed_time, 2),
            },
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except LLMServiceError as e:
        # Handle LLM service specific errors
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="error",
            message="LLM service error during flashcard generation",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "llm_operation": e.operation,
                "llm_error": e.details,
                "status_code": e.status_code,
                "response_time_ms": round(elapsed_time, 2),
            },
        )

        # Map LLM errors to appropriate HTTP status codes
        if e.operation in ["timeout", "api_request", "http_error"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is temporarily unavailable. Please try again later.",
            )
        elif e.operation in ["parse_json", "validate_response", "validate_flashcards"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service returned invalid response. Please try again.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service error occurred. Please try again later.",
            )
    except AIServiceError as e:
        # Handle AI service specific errors
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="error",
            message="AI service error during flashcard generation",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "ai_operation": e.operation,
                "ai_error": e.details,
                "response_time_ms": round(elapsed_time, 2),
            },
        )

        # Map AI service errors to appropriate HTTP status codes
        if "database" in e.details.lower() or "db" in e.operation.lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while processing your request.",
            )
        elif "llm service failed" in e.details.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is temporarily unavailable. Please try again later.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error occurred while processing your request.",
            )
    except ValueError as e:
        # Handle validation errors
        log_with_context(
            level="error",
            message="Input validation error",
            user_id=current_user_id,
            operation=operation,
            extra_context={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid request data provided",
        )
    except Exception as e:
        # Handle unexpected errors with detailed logging
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="error",
            message="Unexpected error during AI flashcard generation",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "response_time_ms": round(elapsed_time, 2),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while generating flashcards",
        )


@router.get(
    "/generation-stats",
    response_model=PaginatedAiGenerationStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI generation statistics",
    description="Get paginated AI generation statistics for the authenticated user. "
    "Returns events tracking flashcard generation with costs, counts, and metadata.",
)
async def get_generation_stats(
    request: Request,
    response: Response,
    current_user_id: Annotated[uuid.UUID, Depends(require_auth_for_ai)],
    ai_generation_service: Annotated[
        AiGenerationService, Depends(get_ai_generation_service_dependency)
    ],
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedAiGenerationStatsResponse:
    """
    Get AI generation statistics for the authenticated user with enhanced security.

    Args:
        request: FastAPI Request object for security analysis
        response: FastAPI Response object for security headers
        page: Page number (starts from 1)
        size: Items per page (max 100)
        current_user_id: Authenticated user ID from JWT
        ai_generation_service: Service for AI generation operations

    Returns:
        Paginated response with AI generation events and metadata

    Raises:
        HTTPException: For various error conditions (400, 401, 500)
    """
    operation = "get_ai_generation_stats"
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
            message="Starting AI generation stats retrieval",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "client_ip": getattr(request.client, "host", "unknown"),
                "user_agent": request.headers.get("user-agent", "unknown")[:100],
                "page": page,
                "size": size,
            },
        )

        # Early return for obvious invalid cases
        if not current_user_id:
            log_with_context(
                level="warning",
                message="Unauthenticated AI stats request",
                operation=operation,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required",
            )

        # Get AI generation statistics using service
        result = await ai_generation_service.get_user_generation_stats(
            user_id=current_user_id, page=page, size=size
        )

        # Log successful retrieval with performance metrics
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="info",
            message="Successfully retrieved AI generation stats",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "total_events": result.total,
                "returned_items": len(result.items),
                "page": result.page,
                "pages": result.pages,
                "response_time_ms": round(elapsed_time, 2),
            },
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except AiGenerationServiceError as e:
        # Handle AI Generation service specific errors
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="error",
            message="AI Generation service error during stats retrieval",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "service_operation": e.operation,
                "service_error": e.details,
                "response_time_ms": round(elapsed_time, 2),
            },
        )

        # Map service errors to appropriate HTTP status codes
        if "database" in e.details.lower() or "query failed" in e.details.lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while retrieving statistics.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error occurred while processing your request.",
            )
    except ValueError as e:
        # Handle validation errors
        log_with_context(
            level="error",
            message="Input validation error",
            user_id=current_user_id,
            operation=operation,
            extra_context={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request parameters provided",
        )
    except Exception as e:
        # Handle unexpected errors with detailed logging
        elapsed_time = (time.time() - start_time) * 1000
        log_with_context(
            level="error",
            message="Unexpected error during AI generation stats retrieval",
            user_id=current_user_id,
            operation=operation,
            extra_context={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "response_time_ms": round(elapsed_time, 2),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving statistics",
        )
