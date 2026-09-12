"""Consent Tracking Manager for Healthcare AI Platform.

Logs patient explicit consent actions, revocation, and maintains auditable consent timelines.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session as DBSession

from app.db.models.consent import Consent as ConsentModel
from app.db.models.audit_log import AuditLog as AuditLogModel


def log_consent_action(
    db: DBSession,
    session_id: uuid.UUID,
    patient_id: uuid.UUID,
    purpose: str = "Pre-consultation clinical history taking and digitization",
    granted: bool = True,
    terms_version: str = "v1.0",
    ip_address: Optional[str] = None,
    signature_hash: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ConsentModel:
    """Record an explicit patient consent grant or revocation action.

    Args:
        db: SQLAlchemy database session
        session_id: Session UUID
        patient_id: Patient UUID
        purpose: Consent scope description
        granted: True if granted, False if revoked
        terms_version: Terms of service version
        ip_address: Client IP address
        signature_hash: SHA-256 digital signature digest
        request_id: Tracing request ID

    Returns:
        Persisted Consent ORM record
    """
    now = datetime.now(timezone.utc)
    consent = ConsentModel(
        id=uuid.uuid4(),
        session_id=session_id,
        patient_id=patient_id,
        purpose=purpose,
        granted=granted,
        terms_version=terms_version,
        signature_hash=signature_hash,
        ip_address=ip_address,
        granted_at=now if granted else None,
        revoked_at=now if not granted else None,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    # Emit audit log record
    action_type = "PATIENT_CONSENT_GRANTED" if granted else "PATIENT_CONSENT_REVOKED"
    audit_entry = AuditLogModel(
        session_id=session_id,
        user_id=str(patient_id),
        action=action_type,
        resource="patient_consent",
        status="SUCCESS",
        details={
            "purpose": purpose,
            "terms_version": terms_version,
            "granted": granted,
            "ip_address": ip_address,
        },
        request_id=request_id or "consent-manager",
    )
    db.add(audit_entry)
    db.commit()

    return consent


def get_audit_trail(
    db: DBSession,
    patient_id: uuid.UUID,
) -> List[Dict[str, Any]]:
    """Retrieve full auditable consent history timeline for a patient.

    Args:
        db: SQLAlchemy database session
        patient_id: Patient UUID

    Returns:
        Chronological list of consent records and audit metadata
    """
    records = (
        db.query(ConsentModel)
        .filter(ConsentModel.patient_id == patient_id)
        .order_by(ConsentModel.created_at.desc())
        .all()
    )

    trail = []
    for r in records:
        trail.append({
            "consent_id": str(r.id),
            "session_id": str(r.session_id),
            "patient_id": str(r.patient_id),
            "purpose": r.purpose,
            "granted": r.granted,
            "terms_version": r.terms_version,
            "ip_address": r.ip_address,
            "granted_at": r.granted_at.isoformat() if r.granted_at else None,
            "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return trail
