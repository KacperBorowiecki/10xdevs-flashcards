from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from src.api.v1.routers.flashcards import router as flashcards_router
from src.api.v1.routers.ai_router import router as ai_router
from src.api.v1.routers.spaced_repetition_router import router as spaced_repetition_router
from src.core.config import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("FastAPI application starting up...")
    logger.info(f"Supabase URL configured: {settings.SUPABASE_URL[:50]}...")
    logger.info(f"LLM Model configured: {settings.LLM_MODEL}")
    yield
    # Shutdown
    logger.info("FastAPI application shutting down...")

# Create FastAPI application
app = FastAPI(
    title="10x-cards API",
    description="API for creating, managing, and studying educational flashcards with AI-powered generation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unexpected error on {request.method} {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include API routers
app.include_router(
    flashcards_router,
    prefix="/api/v1"
)

app.include_router(
    ai_router,
    prefix="/api/v1"
)

app.include_router(
    spaced_repetition_router,
    prefix="/api/v1"
)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "10x-cards API is running"}

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to 10x-cards API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    } 