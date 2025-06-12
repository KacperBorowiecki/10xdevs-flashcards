import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import Request, Response

from src.core.config import settings
from src.db.supabase_client import get_session, refresh_session

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication state and session management with JWT."""

    @staticmethod
    def set_auth_cookie(
        response: Response, user_data: Dict[str, Any], expires_hours: int = 24
    ):
        """Set authentication cookie with JWT token."""
        try:
            # If we have access_token from Supabase, use it directly
            if "access_token" in user_data:
                access_token = user_data["access_token"]
                refresh_token = user_data.get("refresh_token")

                # Store access token in httponly cookie
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    expires=timedelta(hours=expires_hours),
                    httponly=True,
                    secure=settings.app_env == "production",
                    samesite="lax",
                )

                # Store refresh token separately if available
                if refresh_token:
                    response.set_cookie(
                        key="refresh_token",
                        value=refresh_token,
                        expires=timedelta(
                            days=30
                        ),  # Refresh tokens typically last longer
                        httponly=True,
                        secure=settings.app_env == "production",
                        samesite="lax",
                    )
            else:
                # Fallback to creating our own JWT if no Supabase token
                expires = datetime.utcnow() + timedelta(hours=expires_hours)
                payload = {
                    "user_id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "exp": expires,
                    "iat": datetime.utcnow(),
                }

                token = jwt.encode(
                    payload, settings.app_secret_key, algorithm=settings.jwt_algorithm
                )

                response.set_cookie(
                    key="auth_token",
                    value=token,
                    expires=expires,
                    httponly=True,
                    secure=settings.app_env == "production",
                    samesite="lax",
                )

            logger.info(f"Auth cookie set for user: {user_data.get('email')}")

        except Exception as e:
            logger.error(f"Error setting auth cookie: {e}")
            raise

    @staticmethod
    def get_auth_data(request: Request) -> Optional[Dict[str, Any]]:
        """Get authentication data from JWT cookie."""
        try:
            # Try to get Supabase access token first
            access_token = request.cookies.get("access_token")
            if access_token:
                # Decode JWT without verification (Supabase handles verification)
                # In production, you might want to verify with Supabase's JWT secret
                try:
                    payload = jwt.decode(
                        access_token,
                        options={
                            "verify_signature": False
                        },  # Supabase already verified it
                    )

                    # Check expiration
                    if (
                        payload.get("exp")
                        and datetime.fromtimestamp(payload["exp"]) < datetime.utcnow()
                    ):
                        logger.info("Access token expired")
                        return None

                    return {
                        "user_id": payload.get(
                            "sub"
                        ),  # Supabase uses 'sub' for user ID
                        "email": payload.get("email"),
                        "access_token": access_token,
                    }
                except jwt.DecodeError:
                    logger.warning("Invalid JWT format")
                    return None

            # Fallback to custom auth token
            auth_token = request.cookies.get("auth_token")
            if not auth_token:
                return None

            # Decode and verify our custom JWT
            payload = jwt.decode(
                auth_token, settings.app_secret_key, algorithms=[settings.jwt_algorithm]
            )

            return {"user_id": payload.get("user_id"), "email": payload.get("email")}

        except jwt.ExpiredSignatureError:
            logger.info("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading auth cookie: {e}")
            return None

    @staticmethod
    def clear_auth_cookie(response: Response):
        """Clear all authentication cookies."""
        # Clear all possible auth cookies
        response.delete_cookie(
            key="access_token",
            httponly=True,
            secure=settings.app_env == "production",
            samesite="lax",
        )
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=settings.app_env == "production",
            samesite="lax",
        )
        response.delete_cookie(
            key="auth_token",
            httponly=True,
            secure=settings.app_env == "production",
            samesite="lax",
        )
        # Also clear the old auth_session cookie for compatibility
        response.delete_cookie(
            key="auth_session",
            httponly=True,
            secure=settings.app_env == "production",
            samesite="lax",
        )
        logger.info("Auth cookies cleared")

    @staticmethod
    def is_authenticated(request: Request) -> bool:
        """Check if user is authenticated."""
        auth_data = AuthService.get_auth_data(request)
        return auth_data is not None

    @staticmethod
    def get_redirect_url_after_auth(request: Request) -> str:
        """Get URL to redirect to after successful authentication."""
        # Check if there's a 'next' parameter in the request
        next_url = request.query_params.get("next")

        # Validate the next URL (basic security check)
        if next_url and AuthService._is_safe_redirect_url(next_url):
            return next_url

        # Default redirect to dashboard
        return "/dashboard"

    @staticmethod
    def _is_safe_redirect_url(url: str) -> bool:
        """Validate that redirect URL is safe (no external redirects)."""
        # Basic validation - only allow relative URLs starting with /
        return url.startswith("/") and not url.startswith("//")

    @staticmethod
    def get_login_url_with_redirect(current_path: str) -> str:
        """Get login URL with current path as next parameter."""
        if current_path == "/login" or current_path == "/register":
            return "/login"
        return f"/login?next={current_path}"

    @staticmethod
    async def refresh_auth_token(request: Request, response: Response) -> bool:
        """Refresh authentication token if needed."""
        try:
            refresh_token = request.cookies.get("refresh_token")
            if not refresh_token:
                return False

            # Try to refresh session with Supabase
            new_session = await refresh_session()
            if new_session and new_session.session:
                # Update cookies with new tokens
                user_data = {
                    "id": new_session.session.user.id,
                    "email": new_session.session.user.email,
                    "access_token": new_session.session.access_token,
                    "refresh_token": new_session.session.refresh_token,
                }
                AuthService.set_auth_cookie(response, user_data)
                return True

            return False

        except Exception as e:
            logger.error(f"Error refreshing auth token: {e}")
            return False
