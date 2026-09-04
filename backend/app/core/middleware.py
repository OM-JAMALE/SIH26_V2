import time
import uuid
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-MS"] = f"{process_time:.2f}"
            
            # Log request non-sensitively
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code} ({process_time:.2f}ms)",
                extra={"request_id": request_id}
            )
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}",
                exc_info=exc,
                extra={"request_id": request_id}
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "message": "An unexpected internal server error occurred.",
                        "request_id": request_id,
                        "code": "INTERNAL_SERVER_ERROR"
                    }
                },
                headers={"X-Request-ID": request_id}
            )
