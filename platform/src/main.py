"""
Main entry point for the Muppet Platform service.

This module initializes the FastAPI application with proper configuration,
logging, and error handling.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .exceptions import PlatformException
from .logging_config import setup_logging
from .routers import health, mcp, muppets, templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Muppet Platform service v{settings.version}")

    # Initialize async clients
    from .integrations.github import GitHubClient
    from .state_manager import get_state_manager

    # Create and store clients in app state
    github_client = GitHubClient()
    state_manager = get_state_manager()

    app.state.github_client = github_client
    app.state.state_manager = state_manager

    logger.info("Initialized async clients")

    # Initialize state manager by loading muppets from GitHub
    logger.info("Initializing state manager...")
    try:
        await state_manager.initialize()
        logger.info("State manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize state manager: {e}")
        # Continue startup even if state initialization fails
        # The state manager will handle uninitialized state gracefully

    yield

    # Shutdown
    logger.info("Shutting down async clients")
    if hasattr(app.state, "github_client"):
        await app.state.github_client.close()
    logger.info("Shutting down Muppet Platform service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Muppet Platform",
        description="Internal developer platform for creating and managing backend applications",
        version=settings.version,
        lifespan=lifespan,
    )

    # Add CORS middleware
    cors_origins = ["*"] if settings.debug else settings.cors_origins.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(muppets.router, prefix="/api/v1/muppets", tags=["muppets"])
    app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
    app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])

    # Global exception handler
    @app.exception_handler(PlatformException)
    async def platform_exception_handler(request, exc: PlatformException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_type,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTP_ERROR", "message": exc.detail, "details": None},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger = logging.getLogger(__name__)
        logger.exception("Unhandled exception occurred")
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": None,
            },
        )

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
