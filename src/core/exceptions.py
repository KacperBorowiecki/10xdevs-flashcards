from fastapi import HTTPException
from typing import Optional

class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    def __init__(self, message: str = "Nieprawidłowy email lub hasło"):
        super().__init__(message, "INVALID_CREDENTIALS")

class UserAlreadyExistsError(AuthenticationError):
    """Raised when user tries to register with existing email."""
    def __init__(self, message: str = "Użytkownik z tym adresem email już istnieje"):
        super().__init__(message, "USER_ALREADY_EXISTS")

class EmailNotConfirmedError(AuthenticationError):
    """Raised when user tries to login without confirming email."""
    def __init__(self, message: str = "Potwierdź swój adres email, aby się zalogować"):
        super().__init__(message, "EMAIL_NOT_CONFIRMED")

class NetworkError(AuthenticationError):
    """Raised when there's a network/connection issue."""
    def __init__(self, message: str = "Wystąpił błąd połączenia. Spróbuj ponownie."):
        super().__init__(message, "NETWORK_ERROR")

class ValidationError(AuthenticationError):
    """Raised when form validation fails."""
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")

class RateLimitError(AuthenticationError):
    """Raised when too many auth attempts are made."""
    def __init__(self, message: str = "Zbyt wiele prób logowania. Spróbuj ponownie za chwilę."):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")

def auth_exception_to_http(auth_error: AuthenticationError) -> HTTPException:
    """Convert auth exception to HTTP exception for API responses."""
    if isinstance(auth_error, (InvalidCredentialsError, EmailNotConfirmedError)):
        return HTTPException(status_code=401, detail=auth_error.message)
    elif isinstance(auth_error, UserAlreadyExistsError):
        return HTTPException(status_code=409, detail=auth_error.message)
    elif isinstance(auth_error, ValidationError):
        return HTTPException(status_code=422, detail=auth_error.message)
    elif isinstance(auth_error, RateLimitError):
        return HTTPException(status_code=429, detail=auth_error.message)
    elif isinstance(auth_error, NetworkError):
        return HTTPException(status_code=503, detail=auth_error.message)
    else:
        return HTTPException(status_code=500, detail="Wystąpił nieoczekiwany błąd") 