from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import logging
from typing import Annotated, List
from datetime import datetime
import time

from supabase import Client
from src.db.supabase_client import get_supabase_client
from src.services.spaced_repetition_service import SpacedRepetitionService
from src.api.v1.schemas.spaced_repetition_schemas import (
    SpacedRepetitionQueryParams,
    FlashcardWithRepetition,
    SpacedRepetitionReviewRequest,
    SpacedRepetitionReviewResponse,
    ReviewFlashcardCommand
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/spaced-repetition", tags=["spaced-repetition"])

async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: Annotated[Client, Depends(get_supabase_client)]
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

def get_spaced_repetition_service(
    supabase: Annotated[Client, Depends(get_supabase_client)]
) -> SpacedRepetitionService:
    """Dependency to get SpacedRepetitionService instance."""
    return SpacedRepetitionService(supabase)

def add_security_headers(response: Response) -> None:
    """
    Add comprehensive security headers to response.
    
    Args:
        response: FastAPI Response object to add headers to
    """
    # Content security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Additional security headers for API endpoints
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Rate limiting headers (informational)
    response.headers["X-RateLimit-Limit"] = "100"  # 100 requests per minute
    response.headers["X-RateLimit-Window"] = "60"   # 60 seconds

def _validate_request_size(request: Request) -> None:
    """
    Validate request size to prevent abuse.
    
    Args:
        request: FastAPI Request object
        
    Raises:
        HTTPException: If request is too large
    """
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1024:  # 1KB limit for review requests
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Request payload too large"
        )

def _validate_request_headers(request: Request) -> None:
    """
    Validate request headers for security.
    
    Args:
        request: FastAPI Request object
        
    Raises:
        HTTPException: If headers are suspicious
    """
    # Check for suspicious User-Agent patterns
    user_agent = request.headers.get("user-agent", "").lower()
    suspicious_patterns = ["bot", "crawler", "spider", "scraper"]
    
    if any(pattern in user_agent for pattern in suspicious_patterns):
        logger.warning(f"Suspicious User-Agent detected: {user_agent}")
        # Don't block, just log for monitoring

@router.get(
    "/due-cards",
    response_model=List[FlashcardWithRepetition],
    status_code=status.HTTP_200_OK,
    summary="Get due flashcards for review",
    description="Retrieve a list of active flashcards that are due for spaced repetition review. "
                "Returns flashcards with their associated spaced repetition data including due date, "
                "current interval, and last review timestamp. Only authenticated users can access "
                "their own flashcards due to Row Level Security policies."
)
async def get_due_flashcards(
    request: Request,
    response: Response,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    spaced_repetition_service: Annotated[SpacedRepetitionService, Depends(get_spaced_repetition_service)],
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of cards to return (1-100, default: 20)"
    )
) -> List[FlashcardWithRepetition]:
    """
    Get flashcards that are due for spaced repetition review.
    
    This endpoint returns active flashcards that have a due_date <= NOW().
    The flashcards are returned with their complete spaced repetition data
    including due date, current interval, and last review timestamp.
    
    Args:
        request: FastAPI Request object for security analysis
        response: FastAPI Response object for security headers
        current_user_id: Authenticated user ID from JWT token
        spaced_repetition_service: Service for spaced repetition operations
        limit: Maximum number of cards to return (1-100, default: 20)
        
    Returns:
        List of FlashcardWithRepetition objects sorted by due date (earliest first)
        
    Raises:
        HTTPException: For various error conditions (400, 401, 500)
    """
    operation = "get_due_flashcards"
    start_time = time.time()
    
    try:
        # Add security headers
        add_security_headers(response)
        
        # Log request start with context
        logger.info(
            f"Starting spaced repetition due cards retrieval | "
            f"user_id={current_user_id} | limit={limit} | "
            f"client_ip={getattr(request.client, 'host', 'unknown')}"
        )
        
        # Early return for authentication validation
        if not current_user_id:
            logger.warning(f"Unauthenticated request for due cards | operation={operation}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required"
            )
        
        # Validate limit parameter (additional validation beyond Pydantic)
        if not isinstance(limit, int) or not (1 <= limit <= 100):
            logger.warning(
                f"Invalid limit parameter | user_id={current_user_id} | "
                f"limit={limit} | operation={operation}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be an integer between 1 and 100"
            )
        
        # Get due flashcards using service
        due_flashcards = await spaced_repetition_service.get_due_flashcards(
            user_id=current_user_id,
            limit=limit
        )
        
        # Log successful retrieval with performance metrics
        elapsed_time = (time.time() - start_time) * 1000
        logger.info(
            f"Successfully retrieved due flashcards | "
            f"user_id={current_user_id} | count={len(due_flashcards)} | "
            f"response_time_ms={round(elapsed_time, 2)} | operation={operation}"
        )
        
        return due_flashcards
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except ValueError as e:
        logger.warning(
            f"Validation error getting due flashcards | "
            f"user_id={current_user_id} | error={str(e)} | operation={operation}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error getting due flashcards | "
            f"user_id={current_user_id} | error={str(e)} | operation={operation}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while retrieving due flashcards"
        )

@router.post(
    "/reviews",
    response_model=SpacedRepetitionReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit flashcard review result",
    description="""
    Submit a review result for a flashcard with performance rating (1-5).
    
    The spaced repetition algorithm calculates the next review date based on performance rating:
    - **1 = Again**: Reset interval to 1 day (complete failure)
    - **2 = Hard**: Reduce interval by 40% (difficult recall)  
    - **3 = Good**: Increase interval by 30% (standard recall)
    - **4 = Easy**: Double the interval (easy recall)
    - **5 = Perfect**: Increase interval by 250% (perfect recall)
    
    **Rate Limiting**: Maximum 50 reviews per flashcard per 24 hours.
    
    **Request Example**:
    ```json
    {
        "flashcard_id": "123e4567-e89b-12d3-a456-426614174000",
        "performance_rating": 4
    }
    ```
    
    **Response Example**:
    ```json
    {
        "id": "987fcdeb-51a2-43d1-b789-123456789abc",
        "user_id": "456e7890-e89b-12d3-a456-426614174000", 
        "flashcard_id": "123e4567-e89b-12d3-a456-426614174000",
        "due_date": "2024-01-15T10:00:00",
        "current_interval": 6,
        "last_reviewed_at": "2024-01-10T10:00:00",
        "data_extra": {
            "last_performance_rating": 4,
            "review_count": 3,
            "algorithm_version": "sm2_v1"
        },
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-10T10:00:00"
    }
    ```
    
    **Security Features**:
    - JWT authentication required
    - Row Level Security (RLS) enforcement
    - Rate limiting protection
    - Request size validation
    - Comprehensive error handling
    
    Only authenticated users can review their own active flashcards.
    """,
    responses={
        200: {
            "description": "Review processed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "987fcdeb-51a2-43d1-b789-123456789abc",
                        "user_id": "456e7890-e89b-12d3-a456-426614174000",
                        "flashcard_id": "123e4567-e89b-12d3-a456-426614174000",
                        "due_date": "2024-01-15T10:00:00",
                        "current_interval": 6,
                        "last_reviewed_at": "2024-01-10T10:00:00",
                        "data_extra": {
                            "last_performance_rating": 4,
                            "review_count": 3,
                            "algorithm_version": "sm2_v1"
                        },
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-10T10:00:00"
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        401: {"description": "Authentication required"},
        404: {"description": "Flashcard not found or not active"},
        410: {"description": "Flashcard too old for review"},
        413: {"description": "Request payload too large"},
        422: {"description": "Invalid performance rating (must be 1-5)"},
        429: {
            "description": "Rate limit exceeded",
            "headers": {
                "Retry-After": {
                    "description": "Seconds to wait before retry",
                    "schema": {"type": "integer"}
                }
            }
        },
        500: {"description": "Internal server error"}
    }
)
async def submit_flashcard_review(
    request: Request,
    response: Response,
    review_request: SpacedRepetitionReviewRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    spaced_repetition_service: Annotated[SpacedRepetitionService, Depends(get_spaced_repetition_service)]
) -> SpacedRepetitionReviewResponse:
    """
    Submit a flashcard review result and update spaced repetition data.
    
    This endpoint processes a user's performance rating for a flashcard review
    and calculates the next review date using a spaced repetition algorithm.
    The algorithm adjusts the review interval based on the performance rating.
    
    Args:
        request: FastAPI Request object for security analysis
        response: FastAPI Response object for security headers
        review_request: Review data containing flashcard_id and performance_rating
        current_user_id: Authenticated user ID from JWT token
        spaced_repetition_service: Service for spaced repetition operations
        
    Returns:
        Updated spaced repetition record with new due date and interval
        
    Raises:
        HTTPException: For various error conditions (400, 401, 404, 422, 500)
    """
    operation = "submit_flashcard_review"
    start_time = time.time()
    
    try:
        # Add security headers
        add_security_headers(response)
        
        # Security validations
        _validate_request_size(request)
        _validate_request_headers(request)
        
        # Log request start with context
        logger.info(
            f"Starting flashcard review submission | "
            f"user_id={current_user_id} | flashcard_id={review_request.flashcard_id} | "
            f"rating={review_request.performance_rating} | "
            f"client_ip={getattr(request.client, 'host', 'unknown')}"
        )
        
        # Early return for authentication validation
        if not current_user_id:
            logger.warning(f"Unauthenticated request for review submission | operation={operation}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required"
            )
        
        # Validate performance rating (additional validation beyond Pydantic)
        if not isinstance(review_request.performance_rating, int) or not (1 <= review_request.performance_rating <= 5):
            logger.warning(
                f"Invalid performance rating | user_id={current_user_id} | "
                f"rating={review_request.performance_rating} | operation={operation}"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Performance rating must be an integer between 1 and 5"
            )
        
        # Create command object
        review_command = ReviewFlashcardCommand(
            user_id=current_user_id,
            flashcard_id=review_request.flashcard_id,
            performance_rating=review_request.performance_rating
        )
        
        # Process review using service
        review_result = await spaced_repetition_service.review_flashcard(review_command)
        
        # Log successful processing with performance metrics
        elapsed_time = (time.time() - start_time) * 1000
        logger.info(
            f"Successfully processed flashcard review | "
            f"user_id={current_user_id} | flashcard_id={review_request.flashcard_id} | "
            f"new_interval={review_result.current_interval} | "
            f"due_date={review_result.due_date.isoformat()} | "
            f"response_time_ms={round(elapsed_time, 2)} | operation={operation}"
        )
        
        return review_result
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except ValueError as e:
        error_message = str(e)
        
        # Handle specific error cases
        if "not found" in error_message.lower():
            logger.warning(
                f"Flashcard not found | user_id={current_user_id} | "
                f"flashcard_id={review_request.flashcard_id} | operation={operation}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard not found or doesn't belong to user"
            )
        elif "not active" in error_message.lower():
            logger.warning(
                f"Flashcard not active | user_id={current_user_id} | "
                f"flashcard_id={review_request.flashcard_id} | operation={operation}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard is not active"
            )
        elif "too many reviews" in error_message.lower():
            logger.warning(
                f"Rate limit exceeded | user_id={current_user_id} | "
                f"flashcard_id={review_request.flashcard_id} | operation={operation}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "3600"}  # Suggest retry after 1 hour
            )
        elif "too old" in error_message.lower():
            logger.warning(
                f"Flashcard too old for review | user_id={current_user_id} | "
                f"flashcard_id={review_request.flashcard_id} | operation={operation}"
            )
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Flashcard is too old for review"
            )
        else:
            logger.warning(
                f"Validation error in review submission | "
                f"user_id={current_user_id} | error={error_message} | operation={operation}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request: {error_message}"
            )
    except Exception as e:
        logger.error(
            f"Unexpected error in review submission | "
            f"user_id={current_user_id} | flashcard_id={review_request.flashcard_id} | "
            f"error={str(e)} | operation={operation}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing review"
        ) 