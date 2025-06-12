import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.db.supabase_client import get_supabase_client
from src.middleware.auth_middleware import get_current_user
from src.services.auth_service import AuthService
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def require_auth(
    request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Dependency that requires authentication and returns user data."""
    if not current_user:
        # Check if user is authenticated via cookie (fallback)
        if not AuthService.is_authenticated(request):
            logger.info("Unauthenticated user trying to access generate flashcards")
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


@router.get("/generate", response_class=HTMLResponse)
async def generate_flashcards_page(
    request: Request, user_data: Dict[str, Any] = Depends(require_auth)
):
    """
    Render generate flashcards page. Requires authentication.

    Args:
        request: FastAPI request object
        user_data: Authenticated user data from middleware

    Returns:
        HTMLResponse with rendered generate flashcards template
    """
    try:
        user_email = user_data.get("email", "Użytkownik")
        user_id_str = user_data.get("id")

        if not user_id_str:
            logger.error("User ID not found in user data")
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

        logger.info(f"Generate flashcards page accessed by: {user_email}")

        # Prepare template context
        template_context = {
            "request": request,
            "user_email": user_email,
            "user_id": str(user_id_str),
            "current_page": "generate",
        }

        return templates.TemplateResponse("generate_flashcards.html", template_context)

    except HTTPException:
        # Re-raise HTTP exceptions (redirects)
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in generate flashcards page for user {user_email}: {str(e)}"
        )

        # Return template with generic error
        template_context = {
            "request": request,
            "user_email": user_email,
            "user_id": str(user_id_str) if user_id_str else "",
            "current_page": "generate",
            "error_message": "Wystąpił nieoczekiwany błąd. Spróbuj ponownie później.",
        }

        return templates.TemplateResponse("generate_flashcards.html", template_context)
