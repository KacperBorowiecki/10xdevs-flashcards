import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.api.v1.routers.ai_router import get_authenticated_supabase_client
from src.db.supabase_client import get_session, get_supabase_client
from src.dtos import DashboardContext
from src.middleware.auth_middleware import get_current_user
from src.services.auth_service import AuthService
from src.services.dashboard_service import (
    DashboardService,
    DashboardServiceError,
    get_dashboard_service,
)
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_dashboard_service_dependency(
    request: Request, supabase: Client = Depends(get_authenticated_supabase_client)
) -> DashboardService:
    """Dependency to get DashboardService instance with authenticated client."""
    return get_dashboard_service(supabase)


async def require_auth(
    request: Request, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Dependency that requires authentication and returns user data."""
    if not current_user:
        # Check if user is authenticated via cookie (fallback)
        if not AuthService.is_authenticated(request):
            logger.info("Unauthenticated user trying to access protected route")
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


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    dashboard_service: DashboardService = Depends(get_dashboard_service_dependency),
    user_data: Dict[str, Any] = Depends(require_auth),
):
    """
    Render dashboard page with aggregated statistics. Requires authentication.

    Args:
        request: FastAPI request object
        dashboard_service: Injected dashboard service instance
        user_data: Authenticated user data from middleware

    Returns:
        HTMLResponse with rendered dashboard template
    """
    try:
        user_email = user_data.get("email", "Użytkownik")
        user_id_str = user_data.get("id")

        if not user_id_str:
            logger.error("User ID not found in user data")
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

        # Convert user_id string to UUID
        user_id = uuid.UUID(str(user_id_str))

        # Get dashboard context with aggregated statistics
        dashboard_context = await dashboard_service.get_dashboard_context(
            user_id, user_email
        )

        logger.info(
            f"Dashboard accessed by: {user_email} with stats: "
            f"flashcards={dashboard_context.stats.total_flashcards}, "
            f"due={dashboard_context.stats.due_cards_today}, "
            f"ai={dashboard_context.stats.ai_stats.acceptance_ratio}"
        )

        # Prepare template context
        template_context = {
            "request": request,
            "user_email": dashboard_context.user_email,
            "stats": dashboard_context.stats,
            "error_message": dashboard_context.error_message,
        }

        return templates.TemplateResponse("dashboard.html", template_context)

    except ValueError as e:
        logger.error(f"Invalid user ID format: {user_id_str}, error: {str(e)}")
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    except DashboardServiceError as e:
        logger.error(f"Dashboard service error for user {user_email}: {e.details}")

        # Return template with error state
        template_context = {
            "request": request,
            "user_email": user_email,
            "stats": None,
            "error_message": "Wystąpił błąd podczas ładowania dashboard. Spróbuj ponownie.",
        }

        return templates.TemplateResponse("dashboard.html", template_context)
    except HTTPException:
        # Re-raise HTTP exceptions (redirects)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in dashboard for user {user_email}: {str(e)}")

        # Return template with generic error
        template_context = {
            "request": request,
            "user_email": user_email,
            "stats": None,
            "error_message": "Wystąpił nieoczekiwany błąd. Spróbuj ponownie później.",
        }

        return templates.TemplateResponse("dashboard.html", template_context)


@router.get("/api/dashboard/refresh-stats", response_class=JSONResponse)
async def refresh_dashboard_stats(
    request: Request,
    dashboard_service: DashboardService = Depends(get_dashboard_service_dependency),
    user_data: Dict[str, Any] = Depends(require_auth),
):
    """
    API endpoint for refreshing dashboard statistics (used by auto-refresh JavaScript).

    Args:
        request: FastAPI request object
        dashboard_service: Injected dashboard service instance
        user_data: Authenticated user data from middleware

    Returns:
        JSONResponse with refreshed statistics
    """
    try:
        user_email = user_data.get("email", "Unknown")
        user_id_str = user_data.get("id")

        if not user_id_str:
            logger.error("User ID not found in user data for refresh stats")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found"
            )

        # Convert user_id string to UUID
        user_id = uuid.UUID(str(user_id_str))

        # Get fresh dashboard statistics
        dashboard_stats = await dashboard_service.get_dashboard_stats(user_id)

        logger.info(f"Dashboard stats refreshed via API for user: {user_email}")

        # Return JSON response with stats
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Statistics refreshed successfully",
                "stats": {
                    "total_flashcards": dashboard_stats.total_flashcards,
                    "due_cards_today": dashboard_stats.due_cards_today,
                    "ai_stats": {
                        "total_generated": dashboard_stats.ai_stats.total_generated,
                        "total_accepted": dashboard_stats.ai_stats.total_accepted,
                        "acceptance_ratio": dashboard_stats.ai_stats.acceptance_ratio,
                    },
                },
                "timestamp": (
                    dashboard_stats.model_dump()
                    if hasattr(dashboard_stats, "model_dump")
                    else None
                ),
            },
        )

    except ValueError as e:
        logger.error(
            f"Invalid user ID format in refresh stats: {user_id_str}, error: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        )
    except DashboardServiceError as e:
        logger.error(
            f"Dashboard service error in refresh stats for user {user_email}: {e.details}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh statistics",
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in refresh stats for user {user_email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
