import logging

from src.core.config import settings
from supabase import Client, create_client

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Create and return Supabase client instance."""
    try:
        client = create_client(
            supabase_url=settings.supabase_url, supabase_key=settings.supabase_anon_key
        )
        logger.debug("Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise


# Create global client instance
supabase: Client = get_supabase_client()


# Auth helper functions
async def sign_in_with_password(email: str, password: str):
    """Sign in user with email and password."""
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        logger.info(f"User {email} signed in successfully")
        return response
    except Exception as e:
        logger.error(f"Failed to sign in user {email}: {str(e)}")
        raise


async def sign_up(email: str, password: str):
    """Sign up new user with email and password."""
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        logger.info(f"User {email} signed up successfully")
        return response
    except Exception as e:
        logger.error(f"Failed to sign up user {email}: {str(e)}")
        raise


async def sign_out():
    """Sign out current user."""
    try:
        response = supabase.auth.sign_out()
        logger.info("User signed out successfully")
        return response
    except Exception as e:
        logger.error(f"Failed to sign out user: {str(e)}")
        raise


async def get_session():
    """Get current user session."""
    try:
        session = supabase.auth.get_session()
        return session
    except Exception as e:
        logger.error(f"Failed to get session: {str(e)}")
        raise


async def refresh_session():
    """Refresh current session."""
    try:
        session = supabase.auth.refresh_session()
        logger.info("Session refreshed successfully")
        return session
    except Exception as e:
        logger.error(f"Failed to refresh session: {str(e)}")
        raise
