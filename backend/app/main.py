"""
FastAPI Application Entry Point

Initializes:
- CORS configuration (environment-aware)
- Global error handlers (validation, server errors)
- Request/response logging middleware (no clinical data)
- Health check endpoint
- API routers (v1)
- Database session management
"""

import time
import json
import logging
from contextlib import asynccontextmanager
from typing import Callable, Any, Union

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import inspect
import redis

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.middleware import RequestIDMiddleware
from app.core.logging import logger
from app.db.session import engine, Base, SessionLocal
import app.db.models  # Ensure models are imported for metadata creation


# ============================================
# Lifespan Management
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode...")
    
    # Initialize database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Database tables verified.")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise
    
    # Verify database connection
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✓ Database connection verified.")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise
    
    # Verify Redis connection (if configured)
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        logger.info("✓ Redis connection verified.")
    except Exception as e:
        logger.warning(f"⚠ Redis not available: {e}")
    
    yield
    logger.info("Shutting down application...")


# ============================================
# FastAPI Application Setup
# ============================================

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Healthcare AI Pre-consultation Platform - REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ============================================
# CORS Configuration (Environment-Aware)
# ============================================

def get_cors_origins() -> list:
    """
    Get CORS allowed origins based on environment.
    Allows localhost, wildcard (*), and Vercel domains for cloud deployment.
    """
    origins = settings.cors_origins or []
    # Always include wildcard and common deployment origins
    if "*" not in origins:
        origins.extend(["*", "http://localhost:5173", "http://127.0.0.1:5173"])
    return origins

cors_origins = get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

logger.info(f"✓ CORS configured: {len(cors_origins)} allowed origins")


# ============================================
# Custom Middleware: Request ID & Logging
# ============================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    Logs ONLY:
    - Request method, path, status code
    - Response time
    - Request ID for tracing
    
    Does NOT log:
    - Request/response body
    - Clinical data
    - Patient information
    - Sensitive headers
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Log request and response without sensitive data."""
        
        # Extract request info
        request_id = request.headers.get("X-Request-ID", "unknown")
        method = request.method
        path = request.url.path
        start_time = time.time()
        
        # Log request (method/path only)
        logger.info(
            f"[{request_id}] → {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(
                f"[{request_id}] ✗ Request failed: {str(e)}",
                extra={"request_id": request_id}
            )
            raise
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log response (status/time only)
        status_emoji = "✓" if 200 <= status_code < 300 else "✗" if status_code >= 400 else "→"
        logger.info(
            f"[{request_id}] {status_emoji} {method} {path} - {status_code} ({process_time:.3f}s)",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "process_time": process_time,
            }
        )
        
        # Add request ID to response headers (for tracing)
        response.headers["X-Request-ID"] = request_id
        
        return response


# Register custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)

logger.info("✓ Middleware configured: Request ID, Logging")


# ============================================
# Global Error Handlers
# ============================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed error information.
    
    Returns:
    - 422 Unprocessable Entity
    - Error code and description
    - Request ID for tracing
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Extract validation error details
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        f"[{request_id}] Validation error: {len(errors)} field(s) invalid",
        extra={
            "request_id": request_id,
            "error_count": len(errors),
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "code": "VALIDATION_ERROR",
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "errors": errors,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected server errors.
    
    Returns:
    - 500 Internal Server Error
    - Generic error message (no sensitive details)
    - Request ID for debugging
    """
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Log the actual error (server-side only)
    logger.error(
        f"[{request_id}] ✗ Unhandled exception: {type(exc).__name__}",
        exc_info=exc,
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "error_type": type(exc).__name__,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_SERVER_ERROR",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "request_id": request_id,
        },
    )


logger.info("✓ Global error handlers registered")


# ============================================
# Health Check Endpoint
# ============================================

@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="Check application and dependency health status",
    responses={
        200: {
            "description": "All systems operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "database": "ok",
                        "redis": "ok",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        500: {
            "description": "One or more systems down",
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "database": "ok",
                        "redis": "error",
                        "errors": ["Redis unavailable"]
                    }
                }
            }
        }
    }
)
async def health_check() -> dict:
    """
    Check the health of the application and its dependencies.
    
    Returns:
    - status: "ok" (all healthy) or "degraded" (some issues)
    - database: Database connection status
    - redis: Redis connection status
    - errors: List of any detected issues
    """
    health_status = {
        "status": "ok",
        "database": "error",
        "redis": "error",
        "errors": [],
    }
    
    # Check database connection
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["database"] = "ok"
    except Exception as e:
        health_status["database"] = "error"
        health_status["errors"].append(f"Database: {str(e)}")
        logger.warning(f"Health check: Database error - {str(e)}")
    
    # Check Redis connection (optional dependency)
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        health_status["redis"] = "ok"
    except Exception as e:
        health_status["redis"] = "disabled"
        logger.info(f"Health check: Redis optional component not connected")
    
    # Determine overall status (Database is primary requirement)
    if health_status["database"] == "ok":
        health_status["status"] = "ok"
        status_code = 200
    else:
        health_status["status"] = "degraded"
        status_code = 503
    
    return JSONResponse(
        status_code=status_code,
        content=health_status,
    )


logger.info("✓ Health check endpoint registered")


# ============================================
# Root Endpoint
# ============================================

@app.get(
    "/",
    tags=["System"],
    summary="API Root",
    description="API information and documentation links"
)
def root_summary() -> dict:
    """
    Get API information and links to documentation.
    
    Returns:
    - Application name and version
    - Links to Swagger UI, ReDoc, and health check
    """
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "environment": settings.app_env,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api": "/api/v1",
    }


logger.info("✓ Root endpoint registered")


# ============================================
# API Routers
# ============================================

app.include_router(
    api_router,
    prefix="/api/v1",
    tags=["API v1"]
)

logger.info("✓ API v1 router mounted at /api/v1")


# ============================================
# Startup Complete
# ============================================

logger.info(f"✓ {settings.app_name} initialized successfully")
logger.info(f"  Environment: {settings.app_env}")
logger.info(f"  Database: {settings.database_url}")
logger.info(f"  API Docs: http://localhost:8000/docs")
logger.info(f"  Health: http://localhost:8000/health")
