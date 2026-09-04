from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.middleware import RequestIDMiddleware
from app.core.logging import logger
from app.db.session import engine, Base
import app.db.models  # ensure models are imported for metadata creation


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode...")
    # Initialize DB tables for rapid local dev / SQLite test support
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified.")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Custom Middleware
app.add_middleware(RequestIDMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root_summary():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
