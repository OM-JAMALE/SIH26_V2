"""Audit Log repository for security and compliance logging."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import AuditLog
from app.db.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog model (immutable audit trail)."""

    def __init__(self, db: Session):
        """Initialize audit log repository.
        
        Args:
            db: Database session
        """
        super().__init__(AuditLog, db)

    def log_action(
        self,
        action: str,
        resource: str,
        status: str,
        details: Optional[dict] = None,
        session_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """Log an action (immutable audit entry).
        
        Args:
            action: Action name (SESSION_CREATED, DOCUMENT_UPLOADED, etc.)
            resource: Resource type (SESSION, DOCUMENT, PATIENT, etc.)
            status: SUCCESS, FAILURE, or FORBIDDEN
            details: Action details dictionary (no clinical data or credentials)
            session_id: Associated session UUID (optional)
            user_id: User who performed action (optional)
            request_id: Request trace ID (optional)
            
        Returns:
            Created AuditLog instance
        """
        return self.create(
            action=action,
            resource=resource,
            status=status,
            details=details or {},
            session_id=session_id,
            user_id=user_id,
            request_id=request_id
        )

    def get_log(self, log_id: UUID) -> Optional[AuditLog]:
        """Get audit log entry by ID.
        
        Args:
            log_id: Log UUID
            
        Returns:
            AuditLog instance or None
        """
        return self.get(log_id)

    def get_logs_by_session(self, session_id: UUID) -> List[AuditLog]:
        """Get all audit logs for a session (ordered by timestamp descending).
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.session_id == session_id
        ).order_by(desc(AuditLog.created_at)).all()

    def get_logs_by_user(self, user_id: str) -> List[AuditLog]:
        """Get all audit logs by a specific user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(desc(AuditLog.created_at)).all()

    def get_logs_by_action(self, action: str) -> List[AuditLog]:
        """Get all logs for specific action.
        
        Args:
            action: Action name
            
        Returns:
            List of AuditLog instances
        """
        return self.filter(action=action)

    def get_logs_by_resource(self, resource: str) -> List[AuditLog]:
        """Get all logs for specific resource type.
        
        Args:
            resource: Resource type
            
        Returns:
            List of AuditLog instances
        """
        return self.filter(resource=resource)

    def get_logs_by_status(self, status: str) -> List[AuditLog]:
        """Get all logs with specific status.
        
        Args:
            status: SUCCESS, FAILURE, or FORBIDDEN
            
        Returns:
            List of AuditLog instances
        """
        return self.filter(status=status)

    def get_failed_logs(self) -> List[AuditLog]:
        """Get all failed action logs.
        
        Returns:
            List of failed AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.status.in_(["FAILURE", "FORBIDDEN"])
        ).order_by(desc(AuditLog.created_at)).all()

    def get_forbidden_logs(self) -> List[AuditLog]:
        """Get all forbidden action logs (security events).
        
        Returns:
            List of FORBIDDEN AuditLog instances
        """
        return self.filter(status="FORBIDDEN")

    def log_session_created(
        self,
        session_id: UUID,
        user_id: Optional[str] = None
    ) -> AuditLog:
        """Log session creation.
        
        Args:
            session_id: Session UUID
            user_id: User ID (optional)
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            action="SESSION_CREATED",
            resource="SESSION",
            status="SUCCESS",
            details={"session_id": str(session_id)},
            session_id=session_id,
            user_id=user_id
        )

    def log_document_uploaded(
        self,
        session_id: UUID,
        document_id: Optional[str] = None,
        filename: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AuditLog:
        """Log document upload.
        
        Args:
            session_id: Session UUID
            document_id: Document ID (optional)
            filename: Filename (optional)
            user_id: User ID (optional)
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            action="DOCUMENT_UPLOADED",
            resource="DOCUMENT",
            status="SUCCESS",
            details={
                "session_id": str(session_id),
                "document_id": document_id,
                "filename": filename
            },
            session_id=session_id,
            user_id=user_id
        )

    def log_summary_generated(
        self,
        session_id: UUID,
        summary_id: Optional[str] = None,
        model_used: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AuditLog:
        """Log summary generation.
        
        Args:
            session_id: Session UUID
            summary_id: Summary ID (optional)
            model_used: LLM model used (optional)
            user_id: User ID (optional)
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            action="SUMMARY_GENERATED",
            resource="SUMMARY",
            status="SUCCESS",
            details={
                "session_id": str(session_id),
                "summary_id": summary_id,
                "model_used": model_used
            },
            session_id=session_id,
            user_id=user_id
        )

    def log_consent_granted(
        self,
        session_id: UUID,
        patient_id: Optional[str] = None,
        purpose: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Log consent granted.
        
        Args:
            session_id: Session UUID
            patient_id: Patient ID (optional)
            purpose: Consent purpose (optional)
            user_id: User ID (optional)
            ip_address: IP address (optional)
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            action="CONSENT_GRANTED",
            resource="CONSENT",
            status="SUCCESS",
            details={
                "session_id": str(session_id),
                "patient_id": patient_id,
                "purpose": purpose,
                "ip_address": ip_address
            },
            session_id=session_id,
            user_id=user_id
        )

    def log_consent_revoked(
        self,
        session_id: UUID,
        patient_id: Optional[str] = None,
        purpose: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AuditLog:
        """Log consent revoked.
        
        Args:
            session_id: Session UUID
            patient_id: Patient ID (optional)
            purpose: Consent purpose (optional)
            user_id: User ID (optional)
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            action="CONSENT_REVOKED",
            resource="CONSENT",
            status="SUCCESS",
            details={
                "session_id": str(session_id),
                "patient_id": patient_id,
                "purpose": purpose
            },
            session_id=session_id,
            user_id=user_id
        )

    def log_access_denied(
        self,
        action: str,
        resource: str,
        reason: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AuditLog:
        """Log security event (access denied).
        
        Args:
            action: Action attempted
            resource: Resource attempted to access
            reason: Reason for denial
            user_id: User ID (optional)
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            action=action,
            resource=resource,
            status="FORBIDDEN",
            details={"reason": reason},
            user_id=user_id
        )

    def log_error(
        self,
        action: str,
        resource: str,
        error_message: Optional[str] = None,
        session_id: Optional[UUID] = None,
        user_id: Optional[str] = None
    ) -> AuditLog:
        """Log action failure/error.
        
        Args:
            action: Action that failed
            resource: Resource involved
            error_message: Error message (no sensitive data)
            session_id: Session UUID (optional)
            user_id: User ID (optional)
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            action=action,
            resource=resource,
            status="FAILURE",
            details={"error": error_message},
            session_id=session_id,
            user_id=user_id
        )

    def get_security_events(self) -> List[AuditLog]:
        """Get all security events (failures and forbidden actions).
        
        Returns:
            List of security event AuditLog instances
        """
        return self.db.query(AuditLog).filter(
            AuditLog.status.in_(["FAILURE", "FORBIDDEN"])
        ).order_by(desc(AuditLog.created_at)).all()

    def count_logs_by_session(self, session_id: UUID) -> int:
        """Count audit logs for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Number of logs
        """
        return self.count(session_id=session_id)

    def count_logs_by_user(self, user_id: str) -> int:
        """Count audit logs by a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of logs
        """
        return self.count(user_id=user_id)

    def get_session_audit_trail(self, session_id: UUID) -> dict:
        """Get comprehensive audit trail for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Dictionary with audit trail
        """
        logs = self.get_logs_by_session(session_id)
        
        actions_by_type = {}
        for log in logs:
            if log.action not in actions_by_type:
                actions_by_type[log.action] = 0
            actions_by_type[log.action] += 1
        
        failed_count = len([l for l in logs if l.status != "SUCCESS"])
        
        return {
            "session_id": str(session_id),
            "total_log_entries": len(logs),
            "successful_actions": len([l for l in logs if l.status == "SUCCESS"]),
            "failed_actions": failed_count,
            "actions_by_type": actions_by_type,
            "first_action_at": logs[-1].created_at.isoformat() if logs else None,
            "last_action_at": logs[0].created_at.isoformat() if logs else None,
            "timeline": [
                {
                    "timestamp": log.created_at.isoformat(),
                    "action": log.action,
                    "resource": log.resource,
                    "status": log.status,
                    "user": log.user_id
                }
                for log in logs
            ]
        }

    def get_user_activity_report(self, user_id: str) -> dict:
        """Get activity report for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user activity
        """
        logs = self.get_logs_by_user(user_id)
        
        action_counts = {}
        for log in logs:
            if log.action not in action_counts:
                action_counts[log.action] = 0
            action_counts[log.action] += 1
        
        return {
            "user_id": user_id,
            "total_actions": len(logs),
            "successful_actions": len([l for l in logs if l.status == "SUCCESS"]),
            "failed_actions": len([l for l in logs if l.status == "FAILURE"]),
            "forbidden_actions": len([l for l in logs if l.status == "FORBIDDEN"]),
            "actions": action_counts,
            "first_action_at": logs[-1].created_at.isoformat() if logs else None,
            "last_action_at": logs[0].created_at.isoformat() if logs else None
        }

    # Note: delete() is intentionally NOT overridden for AuditLog
    # Audit logs should never be deleted - they are immutable
