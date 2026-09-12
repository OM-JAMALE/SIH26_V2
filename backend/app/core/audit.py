"""Privacy-preserving audit logging module for Healthcare AI Platform.

Ensures sensitive patient clinical content, LLM prompts/outputs, and credentials/tokens 
are strictly redacted before persisting audit event records to the database.
"""

import uuid
from typing import Dict, Any, Optional, Union
from sqlalchemy.orm import Session as DBSession

from app.db.models.audit_log import AuditLog
from app.core.logging import logger

SENSITIVE_KEY_PATTERNS = {
    "text", "content", "patient_text", "clinical_text", "llm_output", "prompt", 
    "raw_text", "transcript", "api_key", "token", "password", "secret", "jwt", 
    "authorization", "bearer", "notes", "description", "summary_text"
}


def sanitize_details(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Recursively scrub sensitive clinical data, LLM text, and credentials from audit details.

    Args:
        details: Raw event metadata dict

    Returns:
        Sanitized metadata dictionary with sensitive fields redacted
    """
    if not details:
        return {}

    sanitized = {}
    for key, value in details.items():
        key_lower = str(key).lower()
        if any(pattern in key_lower for pattern in SENSITIVE_KEY_PATTERNS):
            if "key" in key_lower or "token" in key_lower or "auth" in key_lower or "password" in key_lower or "secret" in key_lower:
                sanitized[key] = "[REDACTED_CREDENTIAL]"
            else:
                sanitized[key] = "[REDACTED_CLINICAL_CONTENT]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_details(value)
        elif isinstance(value, list):
            sanitized_list = []
            for item in value:
                if isinstance(item, dict):
                    sanitized_list.append(sanitize_details(item))
                elif isinstance(item, str) and any(p in key_lower for p in SENSITIVE_KEY_PATTERNS):
                    sanitized_list.append("[REDACTED_CLINICAL_CONTENT]")
                else:
                    sanitized_list.append(item)
            sanitized[key] = sanitized_list
        else:
            sanitized[key] = value

    return sanitized


def log_audit_event(
    db: DBSession,
    action: str,
    resource: str = "system",
    status: str = "SUCCESS",
    session_id: Optional[Union[uuid.UUID, str]] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> AuditLog:
    """Log a privacy-compliant audit record to the database.

    Args:
        db: SQLAlchemy database session
        action: Specific domain action (e.g., "DOC_UPLOAD", "SUMMARY_GEN", "CONSENT_GRANT")
        resource: Target system resource (e.g., "document", "session", "summary")
        status: Operation status ("SUCCESS", "FAILURE", "FORBIDDEN")
        session_id: Optional consultation session UUID or UUID string
        user_id: Optional identifier of acting patient or physician
        details: Optional arbitrary key-value context metadata
        request_id: Optional request correlation ID for tracing

    Returns:
        Persisted AuditLog record
    """
    parsed_session_id = None
    if session_id:
        if isinstance(session_id, uuid.UUID):
            parsed_session_id = session_id
        else:
            try:
                parsed_session_id = uuid.UUID(str(session_id))
            except ValueError:
                parsed_session_id = None

    clean_details = sanitize_details(details)

    audit_record = AuditLog(
        id=uuid.uuid4(),
        session_id=parsed_session_id,
        user_id=user_id or "system",
        action=action,
        resource=resource,
        status=status,
        details=clean_details,
        request_id=request_id or "system-event",
    )

    try:
        db.add(audit_record)
        db.commit()
        db.refresh(audit_record)
    except Exception as ex:
        db.rollback()
        logger.error(f"Failed to persist audit log record: {ex}")
        raise ex

    return audit_record
