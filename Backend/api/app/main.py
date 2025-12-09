"""
TwinSec Studio API - Main application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.core.logging import get_logger

# Import routers
from app.routers import models, attacks, simulations, websocket
# from app.routers import auth, logs

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting TwinSec Studio API", extra={
        "version": settings.VERSION,
        "debug": settings.API_DEBUG
    })
    yield
    # Shutdown
    logger.info("Shutting down TwinSec Studio API")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="OT Cybersecurity Testing Platform with LLM-Powered Model Generation",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-10-01T00:00:00Z"
    }


# Include routers
# app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(models.router, prefix=f"{settings.API_V1_STR}", tags=["Models"])
app.include_router(attacks.router, prefix=f"{settings.API_V1_STR}", tags=["Attacks"])
app.include_router(simulations.router, prefix=f"{settings.API_V1_STR}", tags=["Simulations"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
# app.include_router(logs.router, prefix=f"{settings.API_V1_STR}/logs", tags=["Audit Logs"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
