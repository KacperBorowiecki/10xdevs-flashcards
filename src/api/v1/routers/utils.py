import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, Response, status

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis or similar)
_rate_limit_storage: Dict[str, Dict[str, Any]] = {}


def add_security_headers(response: Response) -> None:
    """
    Add security headers to response.

    Args:
        response: FastAPI Response object to add headers to
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"


def check_rate_limit(
    request: Request, user_id: uuid.UUID, limit: int = 100, window_minutes: int = 60
) -> None:
    """
    Simple rate limiting implementation.

    Args:
        request: FastAPI Request object
        user_id: User UUID for rate limiting
        limit: Number of requests allowed per window
        window_minutes: Time window in minutes

    Raises:
        HTTPException: If rate limit is exceeded
    """
    current_time = datetime.utcnow()
    user_key = str(user_id)

    if user_key not in _rate_limit_storage:
        _rate_limit_storage[user_key] = {"requests": [], "first_request": current_time}

    user_data = _rate_limit_storage[user_key]
    window_start = current_time - timedelta(minutes=window_minutes)

    # Clean old requests
    user_data["requests"] = [
        req_time for req_time in user_data["requests"] if req_time > window_start
    ]

    # Check rate limit
    if len(user_data["requests"]) >= limit:
        log_with_context(
            level="warning",
            message="Rate limit exceeded",
            user_id=user_id,
            operation="rate_limit_check",
            extra_context={
                "client_ip": getattr(request.client, "host", "unknown"),
                "requests_count": len(user_data["requests"]),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests per {window_minutes} minutes.",
            headers={"Retry-After": str(window_minutes * 60)},
        )

    # Add current request
    user_data["requests"].append(current_time)


def validate_request_integrity(request: Request, user_id: uuid.UUID) -> None:
    """
    Validate request integrity and detect potential security issues.

    Args:
        request: FastAPI Request object
        user_id: Authenticated user UUID

    Raises:
        HTTPException: If security validation fails
    """
    # Check for suspicious patterns in user agent
    user_agent = request.headers.get("user-agent", "").lower()
    suspicious_patterns = ["bot", "crawler", "spider", "scraper"]

    if any(pattern in user_agent for pattern in suspicious_patterns):
        log_with_context(
            level="warning",
            message="Suspicious user agent detected",
            user_id=user_id,
            operation="security_check",
            extra_context={
                "user_agent": user_agent,
                "client_ip": getattr(request.client, "host", "unknown"),
            },
        )

    # Additional security checks can be added here
    # e.g., check for common attack patterns in headers


def log_with_context(
    level: str,
    message: str,
    user_id: Optional[uuid.UUID] = None,
    flashcard_id: Optional[uuid.UUID] = None,
    operation: str = "",
    extra_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Structured logging with context information.

    Args:
        level: Log level (info, error, warning, debug)
        message: Log message
        user_id: User UUID for context
        flashcard_id: Flashcard UUID for context
        operation: Operation being performed
        extra_context: Additional context data
    """
    context = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "user_id": str(user_id) if user_id else None,
        "flashcard_id": str(flashcard_id) if flashcard_id else None,
    }

    if extra_context:
        context.update(extra_context)

    # Filter out None values for cleaner logs
    context = {k: v for k, v in context.items() if v is not None}

    log_method = getattr(logger, level.lower(), logger.info)
    log_method(f"{message} | Context: {context}")
