import logging
import json
import sys
from datetime import datetime, timezone
from app.core.config import settings


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("health_ai")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        
    return logger


logger = setup_logging()
