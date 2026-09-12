import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc, or_
from fastapi import HTTPException, status

from app.db.models.patient import Patient as PatientModel
from app.db.models.session import Session as SessionModel
from app.db.models.conversation_turn import ConversationTurn as ConversationTurnModel
from app.db.models.document import Document as DocumentModel
from app.db.models.summary import Summary as SummaryModel
from app.db.models.audit_log import AuditLog as AuditLogModel

from app.modules.patient.schemas import (
    PatientCreateRequest,
    PatientResponse,
    PatientSessionSummaryItem,
    DoctorPatientSearchResult,
    DoctorPatientFullHistory,
)
from app.core.logging import logger


class PatientService:
    """Service handling Patient lifecycle, session history, and Doctor search operations."""

    def _log_audit_event(
        self,
        db: DBSession,
        patient_id: Optional[uuid.UUID],
        action: str,
        resource: str = "patient_record",
        status_code: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        """Log auditable operations without storing raw clinical or sensitive data."""
        audit_log = AuditLogModel(
            session_id=None,
            user_id=str(patient_id) if patient_id else "doctor_search",
            action=action,
            resource=resource,
            status=status_code,
            details=details or {},
            request_id=request_id or "patient-service",
        )
        db.add(audit_log)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to record audit log: {e}")

    def create_or_get_patient(
        self,
        db: DBSession,
        payload: PatientCreateRequest,
        request_id: Optional[str] = None,
    ) -> PatientModel:
        """Create a new patient or retrieve an existing one by ABHA / National Health ID."""
        if payload.national_health_id:
            existing = db.query(PatientModel).filter(
                PatientModel.national_health_id == payload.national_health_id.strip()
            ).first()
            if existing:
                self._log_audit_event(
                    db, existing.id, "RETRIEVE_PATIENT_BY_ABHA", details={"national_health_id": payload.national_health_id}, request_id=request_id
                )
                return existing

        patient = PatientModel(
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            dob=payload.dob.strip(),
            gender=payload.gender.strip(),
            national_health_id=payload.national_health_id.strip() if payload.national_health_id else None,
            contact_number=payload.contact_number.strip() if payload.contact_number else None,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

        self._log_audit_event(
            db, patient.id, "CREATE_PATIENT", details={"has_national_id": bool(patient.national_health_id)}, request_id=request_id
        )
        return patient

    def get_patient(self, db: DBSession, patient_id: uuid.UUID) -> PatientModel:
        """Retrieve patient record by UUID."""
        patient = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID '{patient_id}' not found.",
            )
        return patient

    def get_patient_sessions(
        self, db: DBSession, patient_id: uuid.UUID
    ) -> List[PatientSessionSummaryItem]:
        """Get all past consultation sessions for a returning patient."""
        # Ensure patient exists
        self.get_patient(db, patient_id)

        sessions = (
            db.query(SessionModel)
            .filter(SessionModel.patient_id == patient_id)
            .order_by(desc(SessionModel.created_at))
            .all()
        )

        results = []
        for s in sessions:
            # Calculate counts
            turn_count = db.query(ConversationTurnModel).filter(ConversationTurnModel.session_id == s.id).count()
            doc_count = db.query(DocumentModel).filter(DocumentModel.session_id == s.id).count()

            # Get latest summary if any
            latest_summary = (
                db.query(SummaryModel)
                .filter(SummaryModel.session_id == s.id)
                .order_by(desc(SummaryModel.version))
                .first()
            )

            # Extract chief complaint
            chief_complaint = None
            if latest_summary and latest_summary.chief_complaint:
                chief_complaint = latest_summary.chief_complaint
            elif s.structured_history and isinstance(s.structured_history, dict):
                cc = s.structured_history.get("chief_complaint")
                if isinstance(cc, dict) and cc.get("symptom"):
                    chief_complaint = cc.get("symptom")

            results.append(
                PatientSessionSummaryItem(
                    session_id=str(s.id),
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    mode=s.mode or "MODERN",
                    status=s.status or "INITIATED",
                    lifecycle_status=s.lifecycle_status or "CREATED",
                    current_section=s.current_section or "CHIEF_COMPLAINT",
                    chief_complaint=chief_complaint,
                    safety_status=s.safety_status or "SAFE",
                    turn_count=turn_count,
                    document_count=doc_count,
                    summary_status=latest_summary.workflow_status if latest_summary else "NOT_GENERATED",
                    summary_id=str(latest_summary.id) if latest_summary else None,
                )
            )

        return results

    def search_patients_for_doctor(
        self, db: DBSession, query: str, request_id: Optional[str] = None
    ) -> List[DoctorPatientSearchResult]:
        """Search patients by ABHA ID, Patient UUID, Contact Number, or Name."""
        if not query or not query.strip():
            return []

        cleaned = query.strip()
        conditions = [
            PatientModel.national_health_id.ilike(f"%{cleaned}%"),
            PatientModel.contact_number.ilike(f"%{cleaned}%"),
            PatientModel.first_name.ilike(f"%{cleaned}%"),
            PatientModel.last_name.ilike(f"%{cleaned}%"),
        ]

        # Check if query is a valid UUID
        try:
            uuid_obj = uuid.UUID(cleaned)
            conditions.append(PatientModel.id == uuid_obj)
        except ValueError:
            pass

        patients = db.query(PatientModel).filter(or_(*conditions)).all()

        results = []
        for p in patients:
            sessions = (
                db.query(SessionModel)
                .filter(SessionModel.patient_id == p.id)
                .order_by(desc(SessionModel.created_at))
                .all()
            )
            results.append(
                DoctorPatientSearchResult(
                    id=str(p.id),
                    national_health_id=p.national_health_id,
                    first_name=p.first_name,
                    last_name=p.last_name,
                    dob=p.dob,
                    gender=p.gender,
                    contact_number=p.contact_number,
                    session_count=len(sessions),
                    last_session_at=sessions[0].created_at if sessions else None,
                )
            )

        self._log_audit_event(
            db, None, "DOCTOR_PATIENT_SEARCH", details={"result_count": len(results)}, request_id=request_id
        )
        return results

    def get_full_patient_history(
        self, db: DBSession, patient_id: uuid.UUID, request_id: Optional[str] = None
    ) -> DoctorPatientFullHistory:
        """Get comprehensive historical clinical record for doctor portal."""
        patient_model = self.get_patient(db, patient_id)
        sessions_summary = self.get_patient_sessions(db, patient_id)

        total_docs = db.query(DocumentModel).join(SessionModel).filter(SessionModel.patient_id == patient_id).count()

        patient_resp = PatientResponse(
            id=str(patient_model.id),
            national_health_id=patient_model.national_health_id,
            first_name=patient_model.first_name,
            last_name=patient_model.last_name,
            dob=patient_model.dob,
            gender=patient_model.gender,
            contact_number=patient_model.contact_number,
            created_at=patient_model.created_at,
        )

        self._log_audit_event(
            db, patient_id, "DOCTOR_VIEW_FULL_PATIENT_HISTORY", details={"total_sessions": len(sessions_summary)}, request_id=request_id
        )

        return DoctorPatientFullHistory(
            patient=patient_resp,
            sessions=sessions_summary,
            total_sessions=len(sessions_summary),
            total_documents=total_docs,
        )
