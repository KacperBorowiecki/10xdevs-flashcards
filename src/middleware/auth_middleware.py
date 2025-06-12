from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from src.services.auth_service import AuthService
from src.db.supabase_client import get_session, supabase
import logging
from typing import Callable
import jwt

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Middleware for handling authentication token verification and refresh."""
    
    async def __call__(
        self, 
        request: Request, 
        call_next: Callable
    ):
        """Process authentication for each request."""
        
        # Skip auth for static files and auth routes
        if any(request.url.path.startswith(path) for path in [
            '/static/', '/login', '/register', '/verify-email', '/reset-password'
        ]):
            return await call_next(request)
        
        # Check if user has auth tokens
        auth_data = AuthService.get_auth_data(request)
        
        if auth_data and auth_data.get('access_token'):
            try:
                # Verify token with Supabase
                access_token = auth_data['access_token']
                
                # Try to get current session from Supabase
                supabase.auth.set_session(access_token)
                session = await get_session()
                
                if session and session.session:
                    # Session is valid, continue
                    request.state.user = {
                        'id': session.session.user.id,
                        'email': session.session.user.email,
                        'session': session.session
                    }
                    response = await call_next(request)
                    return response
                else:
                    # Token might be expired, try to refresh
                    logger.info("Access token expired, attempting refresh")
                    
                    # Create temporary response to handle cookies
                    temp_response = Response()
                    if await AuthService.refresh_auth_token(request, temp_response):
                        # Refresh successful, retry with new token
                        response = await call_next(request)
                        
                        # Copy cookies from temp response
                        for cookie in temp_response.raw_headers:
                            if cookie[0] == b'set-cookie':
                                response.raw_headers.append(cookie)
                        
                        return response
                    else:
                        # Refresh failed, clear cookies
                        logger.warning("Token refresh failed, clearing auth")
                        response = await call_next(request)
                        AuthService.clear_auth_cookie(response)
                        return response
                        
            except jwt.ExpiredSignatureError:
                logger.info("JWT expired, attempting refresh")
                
                # Try to refresh token
                temp_response = Response()
                if await AuthService.refresh_auth_token(request, temp_response):
                    response = await call_next(request)
                    # Copy cookies from temp response
                    for cookie in temp_response.raw_headers:
                        if cookie[0] == b'set-cookie':
                            response.raw_headers.append(cookie)
                    return response
                    
            except Exception as e:
                logger.error(f"Auth middleware error: {str(e)}")
        
        # Continue without auth for public routes
        response = await call_next(request)
        return response


async def get_current_user(request: Request):
    """Dependency to get current user from request state."""
    if hasattr(request.state, 'user'):
        return request.state.user
    return None 