from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

router = APIRouter()


@router.get("", summary="Comprehensive System Health Check")
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    # Check Database
    db_status = "healthy"
    db_error = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
        db_error = str(e)

    # Check Redis
    redis_status = "healthy"
    redis_error = None
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        r.ping()
    except Exception as e:
        redis_status = "unhealthy"
        redis_error = str(e)

    overall_healthy = (db_status == "healthy") and (redis_status == "healthy")

    response_data = {
        "status": "healthy" if overall_healthy else "degraded",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "ai_provider": settings.ai_provider,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": {"status": db_status, "error": db_error},
            "redis": {"status": redis_status, "error": redis_error},
        },
    }

    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=response_data)


@router.get("/db", summary="Database Connectivity Health Check")
def db_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        res = db.execute(text("SELECT 1")).scalar()
        return {"status": "healthy", "database": "postgresql/sqlite", "result": res}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)},
        )


@router.get("/redis", summary="Redis Connectivity Health Check")
def redis_health_check() -> Dict[str, Any]:
    try:
        import redis
        r = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        ping_res = r.ping()
        return {"status": "healthy", "redis_ping": ping_res}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)},
        )
