import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.api.v1.routers.ai_router import get_authenticated_supabase_client
from src.api.v1.schemas.flashcard_schemas import (
    FlashcardSourceEnum,
    FlashcardStatusEnum,
    ListFlashcardsQueryParams,
    PaginatedFlashcardsResponse,
)
from src.db.supabase_client import get_supabase_client
from src.dtos import (
    FlashcardManualCreateRequest,
    FlashcardPatchRequest,
    FlashcardResponse,
    PaginatedResponse,
)
from src.middleware.auth_middleware import get_current_user
from src.services.auth_service import AuthService
from src.services.flashcard_service import FlashcardService
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_flashcard_service_dependency(
    request: Request, supabase: Client = Depends(get_authenticated_supabase_client)
) -> FlashcardService:
    """Dependency to get FlashcardService instance with authenticated client."""
    return FlashcardService(supabase)


async def require_auth(
    request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Dependency that requires authentication and returns user data."""
    if not current_user:
        # Check if user is authenticated via cookie (fallback)
        if not AuthService.is_authenticated(request):
            logger.info("Unauthenticated user trying to access flashcards view")
            login_url = AuthService.get_login_url_with_redirect(request.url.path)
            raise HTTPException(
                status_code=status.HTTP_302_FOUND, headers={"Location": login_url}
            )

        # Get user data from auth cookie (fallback)
        auth_data = AuthService.get_auth_data(request)
        if not auth_data:
            raise HTTPException(
                status_code=status.HTTP_302_FOUND, headers={"Location": "/login"}
            )

        return {"id": auth_data.get("user_id"), "email": auth_data.get("email")}

    return current_user


@router.get("/flashcards", response_class=HTMLResponse)
async def flashcards_view(
    request: Request,
    source: Optional[str] = Query(
        None, description="Filter by flashcard source (manual, ai_suggestion)"
    ),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    flashcard_service: FlashcardService = Depends(get_flashcard_service_dependency),
    user_data: Dict[str, Any] = Depends(require_auth),
):
    """
    Render 'Moje fiszki' page with user's flashcards. Supports filtering and pagination.

    Args:
        request: FastAPI request object
        source: Optional source filter (manual, ai_suggestion)
        page: Page number for pagination (default: 1)
        size: Number of items per page (default: 20, max: 100)
        flashcard_service: Injected flashcard service instance
        user_data: Authenticated user data from middleware

    Returns:
        HTMLResponse with rendered my_flashcards template
    """
    try:
        user_email = user_data.get("email", "Użytkownik")
        user_id_str = user_data.get("id")

        if not user_id_str:
            logger.error("User ID not found in user data")
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

        # Convert user_id string to UUID
        user_id = uuid.UUID(str(user_id_str))

        # Parse and validate source filter
        source_filter = None
        if source:
            try:
                source_filter = FlashcardSourceEnum(source)
            except ValueError:
                logger.warning(f"Invalid source filter: {source}")
                # Reset to None for invalid values
                source_filter = None

        # Create query parameters
        query_params = ListFlashcardsQueryParams(
            status=FlashcardStatusEnum.ACTIVE,  # Always show only active flashcards
            source=source_filter,
            page=page,
            size=size,
        )

        # Get flashcards using service
        flashcards_response = flashcard_service.get_flashcards_for_user(
            user_id=user_id, params=query_params
        )

        logger.info(
            f"Flashcards view accessed by: {user_email}, "
            f"page={page}, size={size}, source={source}, "
            f"found={len(flashcards_response.items)} flashcards"
        )

        # Prepare template context
        template_context = {
            "request": request,
            "user_email": user_email,
            "flashcards": flashcards_response,
            "current_filter": {"source": source, "page": page, "size": size},
            "available_sources": [
                {"value": "", "label": "Wszystkie"},
                {"value": "manual", "label": "Ręczne"},
                {"value": "ai_suggestion", "label": "Wygenerowane przez AI"},
            ],
        }

        return templates.TemplateResponse("my_flashcards.html", template_context)

    except ValueError as e:
        logger.error(f"Invalid user ID format: {user_id_str}, error: {str(e)}")
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        logger.error(
            f"Unexpected error in flashcards view for user {user_email}: {str(e)}"
        )

        # Return template with error state
        template_context = {
            "request": request,
            "user_email": user_email,
            "flashcards": None,
            "current_filter": {"source": source, "page": page, "size": size},
            "error_message": "Wystąpił błąd podczas ładowania fiszek. Spróbuj ponownie.",
            "available_sources": [
                {"value": "", "label": "Wszystkie"},
                {"value": "manual", "label": "Ręczne"},
                {"value": "ai_suggestion", "label": "Wygenerowane przez AI"},
            ],
        }

        return templates.TemplateResponse("my_flashcards.html", template_context)
