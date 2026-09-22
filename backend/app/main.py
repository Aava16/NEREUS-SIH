from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router, v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for non-destructive startup & graceful shutdown."""
    setup_logging(debug=settings.debug)
    logger.info("Initializing %s v%s...", settings.app_name, settings.app_version)
    logger.info("Configuration loaded from backend environment.")
    yield
    logger.info("Shutting down %s...", settings.app_name)


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers
    app.include_router(api_router)
    app.include_router(v1_router)

    return app


app = create_application()
