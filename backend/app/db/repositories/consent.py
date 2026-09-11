"""Consent repository for consent and privacy audit operations."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import Consent
from app.db.repositories.base import BaseRepository


class ConsentRepository(BaseRepository[Consent]):
    """Repository for Consent model."""

    def __init__(self, db: Session):
        """Initialize consent repository.
        
        Args:
            db: Database session
        """
        super().__init__(Consent, db)

    def log_consent(
        self,
        session_id: UUID,
        patient_id: UUID,
        purpose: str,
        granted: bool = True,
        terms_version: str = "v1.0",
        signature_hash: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Consent:
        """Log a consent action (immutable audit trail).
        
        Args:
            session_id: Session UUID
            patient_id: Patient UUID
            purpose: Consent purpose (data_sharing, abdm_integration, fhir_export, etc.)
            granted: Whether consent is granted
            terms_version: Terms version
            signature_hash: Hash of signature if applicable
            ip_address: IP address of consent action
            
        Returns:
            Created Consent instance
        """
        return self.create(
            session_id=session_id,
            patient_id=patient_id,
            purpose=purpose,
            granted=granted,
            terms_version=terms_version,
            signature_hash=signature_hash,
            ip_address=ip_address,
            granted_at=datetime.now(timezone.utc) if granted else None
        )

    def get_consent(self, consent_id: UUID) -> Optional[Consent]:
        """Get consent record by ID.
        
        Args:
            consent_id: Consent UUID
            
        Returns:
            Consent instance or None
        """
        return self.get(consent_id)

    def get_consent_history(
        self,
        patient_id: UUID
    ) -> List[Consent]:
        """Get all consent records for a patient (audit trail).
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            List of Consent instances (ordered by creation time descending)
        """
        return self.db.query(Consent).filter(
            Consent.patient_id == patient_id
        ).order_by(desc(Consent.created_at)).all()

    def get_session_consents(self, session_id: UUID) -> List[Consent]:
        """Get all consent records for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of Consent instances
        """
        return self.filter(session_id=session_id)

    def get_active_consents(self, patient_id: UUID) -> List[Consent]:
        """Get currently active (granted, not revoked) consents for patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            List of active Consent instances
        """
        return self.db.query(Consent).filter(
            Consent.patient_id == patient_id,
            Consent.granted == True,
            Consent.revoked_at == None
        ).all()

    def get_revoked_consents(self, patient_id: UUID) -> List[Consent]:
        """Get revoked consents for patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            List of revoked Consent instances
        """
        return self.db.query(Consent).filter(
            Consent.patient_id == patient_id,
            Consent.revoked_at != None
        ).all()

    def get_consent_by_purpose(
        self,
        patient_id: UUID,
        purpose: str
    ) -> Optional[Consent]:
        """Get latest consent record for specific purpose.
        
        Args:
            patient_id: Patient UUID
            purpose: Consent purpose
            
        Returns:
            Consent instance or None
        """
        return self.db.query(Consent).filter(
            Consent.patient_id == patient_id,
            Consent.purpose == purpose
        ).order_by(desc(Consent.created_at)).first()

    def has_active_consent(
        self,
        patient_id: UUID,
        purpose: str
    ) -> bool:
        """Check if patient has active consent for purpose.
        
        Args:
            patient_id: Patient UUID
            purpose: Consent purpose
            
        Returns:
            True if active consent exists
        """
        consent = self.db.query(Consent).filter(
            Consent.patient_id == patient_id,
            Consent.purpose == purpose,
            Consent.granted == True,
            Consent.revoked_at == None
        ).first()
        return consent is not None

    def revoke_consent(
        self,
        consent_id: UUID
    ) -> Optional[Consent]:
        """Revoke a consent (marks as revoked, doesn't delete).
        
        Args:
            consent_id: Consent UUID
            
        Returns:
            Updated Consent instance or None
        """
        return self.update(
            consent_id,
            revoked_at=datetime.now(timezone.utc)
        )

    def revoke_all_consents_by_purpose(
        self,
        patient_id: UUID,
        purpose: str
    ) -> int:
        """Revoke all active consents for a specific purpose.
        
        Args:
            patient_id: Patient UUID
            purpose: Consent purpose
            
        Returns:
            Number of revoked consents
        """
        consents = self.db.query(Consent).filter(
            Consent.patient_id == patient_id,
            Consent.purpose == purpose,
            Consent.granted == True,
            Consent.revoked_at == None
        ).all()
        
        count = 0
        for consent in consents:
            if self.revoke_consent(consent.id):
                count += 1
        return count

    def grant_consent(
        self,
        session_id: UUID,
        patient_id: UUID,
        purpose: str,
        terms_version: str = "v1.0",
        signature_hash: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Consent:
        """Grant new consent (logs as granted).
        
        Args:
            session_id: Session UUID
            patient_id: Patient UUID
            purpose: Consent purpose
            terms_version: Terms version
            signature_hash: Signature hash (optional)
            ip_address: IP address (optional)
            
        Returns:
            Created Consent instance
        """
        return self.log_consent(
            session_id=session_id,
            patient_id=patient_id,
            purpose=purpose,
            granted=True,
            terms_version=terms_version,
            signature_hash=signature_hash,
            ip_address=ip_address
        )

    def deny_consent(
        self,
        session_id: UUID,
        patient_id: UUID,
        purpose: str,
        terms_version: str = "v1.0",
        ip_address: Optional[str] = None
    ) -> Consent:
        """Deny consent (logs as not granted).
        
        Args:
            session_id: Session UUID
            patient_id: Patient UUID
            purpose: Consent purpose
            terms_version: Terms version
            ip_address: IP address (optional)
            
        Returns:
            Created Consent instance
        """
        return self.log_consent(
            session_id=session_id,
            patient_id=patient_id,
            purpose=purpose,
            granted=False,
            terms_version=terms_version,
            ip_address=ip_address
        )

    def delete_consent(self, consent_id: UUID) -> bool:
        """Delete consent record (rarely used; typically revoke instead).
        
        Args:
            consent_id: Consent UUID
            
        Returns:
            True if deleted
        """
        return self.delete(consent_id)

    def consent_exists(self, consent_id: UUID) -> bool:
        """Check if consent record exists.
        
        Args:
            consent_id: Consent UUID
            
        Returns:
            True if exists
        """
        return self.exists(id=consent_id)

    def count_consents_by_patient(self, patient_id: UUID) -> int:
        """Count all consent records for a patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Number of consent records
        """
        return self.count(patient_id=patient_id)

    def count_active_consents(self, patient_id: UUID) -> int:
        """Count active (granted, not revoked) consents for patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Number of active consents
        """
        return self.db.query(Consent).filter(
            Consent.patient_id == patient_id,
            Consent.granted == True,
            Consent.revoked_at == None
        ).count()

    def get_consent_audit_trail(self, patient_id: UUID) -> dict:
        """Get comprehensive consent audit trail for patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Dictionary with consent audit information
        """
        all_consents = self.get_consent_history(patient_id)
        active_consents = self.get_active_consents(patient_id)
        revoked_consents = self.get_revoked_consents(patient_id)
        
        # Group by purpose
        by_purpose = {}
        for consent in all_consents:
            if consent.purpose not in by_purpose:
                by_purpose[consent.purpose] = []
            by_purpose[consent.purpose].append({
                "id": str(consent.id),
                "granted": consent.granted,
                "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
                "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
                "terms_version": consent.terms_version,
                "ip_address": consent.ip_address
            })
        
        return {
            "patient_id": str(patient_id),
            "total_consent_records": len(all_consents),
            "active_count": len(active_consents),
            "revoked_count": len(revoked_consents),
            "by_purpose": by_purpose,
            "active_purposes": [c.purpose for c in active_consents],
            "first_consent_at": all_consents[-1].created_at.isoformat() if all_consents else None,
            "last_consent_at": all_consents[0].created_at.isoformat() if all_consents else None
        }

    def get_purpose_stats(self, patient_id: UUID) -> dict:
        """Get statistics on consent purposes for patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Dictionary with purpose statistics
        """
        all_consents = self.get_consent_history(patient_id)
        
        purpose_stats = {}
        for consent in all_consents:
            if consent.purpose not in purpose_stats:
                purpose_stats[consent.purpose] = {
                    "total": 0,
                    "granted": 0,
                    "denied": 0,
                    "active": 0
                }
            
            purpose_stats[consent.purpose]["total"] += 1
            if consent.granted:
                purpose_stats[consent.purpose]["granted"] += 1
                if consent.revoked_at is None:
                    purpose_stats[consent.purpose]["active"] += 1
            else:
                purpose_stats[consent.purpose]["denied"] += 1
        
        return {
            "patient_id": str(patient_id),
            "purposes": purpose_stats
        }
