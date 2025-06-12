from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field, ValidationError as PydanticValidationError
from typing import Optional
import logging
import re

from src.core.exceptions import (
    AuthenticationError, 
    InvalidCredentialsError, 
    UserAlreadyExistsError,
    EmailNotConfirmedError,
    NetworkError,
    ValidationError as AuthValidationError,
    auth_exception_to_http
)
from src.services.auth_service import AuthService
from src.db.supabase_client import sign_in_with_password, sign_up

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Validation models
class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="User password")

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="User password")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="Password confirmation")
    
    def validate_passwords_match(self) -> bool:
        return self.password == self.confirm_password

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Render login page. Redirect to dashboard if already authenticated."""
    # Check if user is already authenticated
    if AuthService.is_authenticated(request):
        redirect_url = AuthService.get_redirect_url_after_auth(request)
        logger.info("User already authenticated, redirecting to dashboard")
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "auth.html", 
        {
            "request": request, 
            "mode": "login",
            "error_message": error
        }
    )

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, error: Optional[str] = None):
    """Render register page. Redirect to dashboard if already authenticated."""
    # Check if user is already authenticated
    if AuthService.is_authenticated(request):
        redirect_url = AuthService.get_redirect_url_after_auth(request)
        logger.info("User already authenticated, redirecting to dashboard")
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "auth.html", 
        {
            "request": request, 
            "mode": "register",
            "error_message": error
        }
    )

@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission with comprehensive error handling."""
    try:
        # Validate input data
        login_data = LoginRequest(email=email, password=password)
        
        logger.info(f"Login attempt for email: {login_data.email}")
        
        # Authenticate with Supabase
        try:
            auth_response = await sign_in_with_password(
                email=login_data.email,
                password=login_data.password
            )
            
            # Check if authentication was successful
            if auth_response.user is None:
                raise InvalidCredentialsError()
            
            # Check if email is confirmed
            if hasattr(auth_response.user, 'email_confirmed_at') and auth_response.user.email_confirmed_at is None:
                raise EmailNotConfirmedError()
            
            logger.info(f"Successful login for: {login_data.email}")
            
            # Extract user data from Supabase response
            user_data = {
                'id': str(auth_response.user.id),
                'email': auth_response.user.email,
                'access_token': auth_response.session.access_token if auth_response.session else None,
                'refresh_token': auth_response.session.refresh_token if auth_response.session else None
            }
            
        except Exception as supabase_error:
            # Handle Supabase-specific errors
            error_message = str(supabase_error).lower()
            if "invalid" in error_message or "credentials" in error_message:
                raise InvalidCredentialsError()
            elif "network" in error_message or "connection" in error_message:
                raise NetworkError()
            else:
                logger.error(f"Supabase auth error: {supabase_error}")
                raise AuthenticationError("Wystąpił błąd podczas logowania")
        
        # Get redirect URL
        redirect_url = AuthService.get_redirect_url_after_auth(request)
        
        # Create response with redirect
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        
        # Set auth cookie
        AuthService.set_auth_cookie(response, user_data)
        
        return response
        
    except PydanticValidationError as e:
        logger.warning(f"Validation error during login: {e}")
        error_message = "Nieprawidłowe dane formularza"
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "mode": "login", "error_message": error_message}
        )
    except AuthenticationError as e:
        logger.warning(f"Authentication error during login: {e.message}")
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "mode": "login", "error_message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        error_message = "Wystąpił nieoczekiwany błąd. Spróbuj ponownie."
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "mode": "login", "error_message": error_message}
        )

@router.post("/register")
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handle register form submission with comprehensive error handling.
    
    For POC/Local development: Accounts are automatically activated and users are logged in immediately.
    Email verification is disabled for local development simplicity.
    """
    try:
        # Validate input data
        register_data = RegisterRequest(
            email=email, 
            password=password, 
            confirm_password=confirm_password
        )
        
        # Validate password match
        if not register_data.validate_passwords_match():
            raise AuthValidationError("confirm_password", "Hasła nie są identyczne")
        
        logger.info(f"Registration attempt for email: {register_data.email}")
        
        # Register with Supabase
        try:
            auth_response = await sign_up(
                email=register_data.email,
                password=register_data.password
            )
            
            # Check if registration was successful
            if auth_response.user is None:
                # This might happen if the user already exists
                raise UserAlreadyExistsError()
            
            logger.info(f"Successful registration for: {register_data.email}")
            
            # POC/Local Development: Auto-activate account and log user in immediately
            # Email verification is skipped for local development simplicity
            
            # Extract user data from Supabase response
            user_data = {
                'id': str(auth_response.user.id),
                'email': auth_response.user.email,
                'access_token': auth_response.session.access_token if auth_response.session else None,
                'refresh_token': auth_response.session.refresh_token if auth_response.session else None
            }
            
            # Get redirect URL (should go to dashboard)
            redirect_url = AuthService.get_redirect_url_after_auth(request)
            
            # Create response with redirect to dashboard
            response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
            
            # Set auth cookie to log user in immediately
            AuthService.set_auth_cookie(response, user_data)
            
            logger.info(f"User {register_data.email} registered and logged in automatically")
            return response
                
        except Exception as supabase_error:
            # Handle Supabase-specific errors
            error_message = str(supabase_error).lower()
            if "already registered" in error_message or "already exists" in error_message:
                raise UserAlreadyExistsError()
            elif "network" in error_message or "connection" in error_message:
                raise NetworkError()
            else:
                logger.error(f"Supabase registration error: {supabase_error}")
                raise AuthenticationError("Wystąpił błąd podczas rejestracji")
        
    except PydanticValidationError as e:
        logger.warning(f"Validation error during registration: {e}")
        error_message = "Nieprawidłowe dane formularza"
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "mode": "register", "error_message": error_message}
        )
    except AuthValidationError as e:
        logger.warning(f"Custom validation error during registration: {e.message}")
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "mode": "register", "error_message": e.message}
        )
    except AuthenticationError as e:
        logger.warning(f"Authentication error during registration: {e.message}")
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "mode": "register", "error_message": e.message}
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        error_message = "Wystąpił nieoczekiwany błąd. Spróbuj ponownie."
        return templates.TemplateResponse(
            "auth.html",
            {"request": request, "mode": "register", "error_message": error_message}
        )

@router.post("/logout")
async def logout(request: Request):
    """Handle user logout."""
    try:
        logger.info("User logout initiated")
        
        # Create response with redirect to login
        response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
        # Clear auth cookie
        AuthService.clear_auth_cookie(response)
        
        logger.info("User successfully logged out")
        return response
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}", exc_info=True)
        # Even if there's an error, redirect to login
        response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        AuthService.clear_auth_cookie(response)
        return response

@router.get("/logout")
async def logout_get(request: Request):
    """Handle logout via GET request (for convenience)."""
    return await logout(request)

@router.get("/verify-email")
async def verify_email(
    request: Request,
    token: str,
    type: Optional[str] = "signup"
):
    """
    Handle email verification with token from email link.
    
    NOTE: For POC/Local development this functionality is not needed as accounts 
    are auto-activated during registration. This endpoint is kept for future production use.
    
    Args:
        request: FastAPI request object
        token: Verification token from email
        type: Type of verification (signup, recovery, etc.)
    """
    try:
        logger.info(f"Email verification attempt with token type: {type}")
        
        # Verify the token with Supabase
        from src.db.supabase_client import supabase
        
        if type == "recovery":
            # Handle password recovery token
            return templates.TemplateResponse(
                "reset_password.html",
                {"request": request, "token": token, "error_message": None}
            )
        else:
            # Handle email confirmation
            try:
                # Supabase automatically handles email verification via the token
                # The user just needs to visit this URL with the token
                success_message = "Email został pomyślnie zweryfikowany! Możesz się teraz zalogować."
                
                return templates.TemplateResponse(
                    "auth.html",
                    {
                        "request": request, 
                        "mode": "login", 
                        "success_message": success_message,
                        "error_message": None
                    }
                )
            except Exception as e:
                logger.error(f"Email verification error: {str(e)}")
                error_message = "Link weryfikacyjny jest nieprawidłowy lub wygasł."
                return templates.TemplateResponse(
                    "auth.html",
                    {
                        "request": request, 
                        "mode": "login", 
                        "error_message": error_message
                    }
                )
                
    except Exception as e:
        logger.error(f"Unexpected error in email verification: {str(e)}")
        return templates.TemplateResponse(
            "auth.html",
            {
                "request": request, 
                "mode": "login", 
                "error_message": "Wystąpił błąd podczas weryfikacji emaila."
            }
        )

@router.post("/resend-verification")
async def resend_verification_email(
    request: Request,
    email: str = Form(...)
):
    """Handle resending verification email.
    
    NOTE: For POC/Local development this functionality is not needed as accounts 
    are auto-activated during registration. This endpoint is kept for future production use.
    """
    try:
        logger.info(f"Resend verification email requested for: {email}")
        
        from src.db.supabase_client import supabase
        
        # Resend verification email via Supabase
        response = supabase.auth.resend({
            "type": "signup",
            "email": email
        })
        
        success_message = "Email weryfikacyjny został wysłany ponownie. Sprawdź swoją skrzynkę."
        return templates.TemplateResponse(
            "auth.html",
            {
                "request": request,
                "mode": "login",
                "success_message": success_message
            }
        )
        
    except Exception as e:
        logger.error(f"Error resending verification email: {str(e)}")
        error_message = "Nie udało się wysłać emaila weryfikacyjnego. Spróbuj ponownie później."
        return templates.TemplateResponse(
            "auth.html",
            {
                "request": request,
                "mode": "login",
                "error_message": error_message
            }
        )

@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...)
):
    """Handle forgot password request.
    
    NOTE: For POC/Local development this functionality can be skipped.
    Users can simply create new accounts. This endpoint is kept for future production use.
    """
    try:
        logger.info(f"Password reset requested for: {email}")
        
        from src.db.supabase_client import supabase
        
        # Request password reset via Supabase
        response = supabase.auth.reset_password_email(
            email=email,
            redirect_to=f"{request.base_url}verify-email"
        )
        
        # Always show success message to prevent email enumeration
        success_message = "Jeśli podany adres email istnieje w naszej bazie, otrzymasz link do resetowania hasła."
        
        return templates.TemplateResponse(
            "auth.html",
            {
                "request": request,
                "mode": "login",
                "success_message": success_message
            }
        )
        
    except Exception as e:
        logger.error(f"Error in forgot password: {str(e)}")
        error_message = "Wystąpił błąd podczas wysyłania emaila. Spróbuj ponownie później."
        return templates.TemplateResponse(
            "auth.html",
            {
                "request": request,
                "mode": "login",
                "error_message": error_message
            }
        )

@router.post("/reset-password")
async def reset_password_submit(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handle password reset form submission.
    
    NOTE: For POC/Local development this functionality can be skipped.
    Users can simply create new accounts. This endpoint is kept for future production use.
    """
    try:
        # Validate passwords match
        if password != confirm_password:
            return templates.TemplateResponse(
                "reset_password.html",
                {
                    "request": request,
                    "token": token,
                    "error_message": "Hasła nie są identyczne"
                }
            )
        
        # Validate password strength
        if len(password) < 6:
            return templates.TemplateResponse(
                "reset_password.html",
                {
                    "request": request,
                    "token": token,
                    "error_message": "Hasło musi mieć co najmniej 6 znaków"
                }
            )
        
        from src.db.supabase_client import supabase
        
        # Update password using the token
        response = supabase.auth.update_user({
            "password": password
        })
        
        if response.user:
            logger.info(f"Password reset successful for user: {response.user.email}")
            success_message = "Hasło zostało pomyślnie zmienione! Możesz się teraz zalogować."
            
            return templates.TemplateResponse(
                "auth.html",
                {
                    "request": request,
                    "mode": "login",
                    "success_message": success_message
                }
            )
        else:
            raise Exception("Failed to reset password")
            
    except Exception as e:
        logger.error(f"Error in password reset: {str(e)}")
        error_message = "Link resetowania hasła jest nieprawidłowy lub wygasł."
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "token": token,
                "error_message": error_message
            }
        ) 