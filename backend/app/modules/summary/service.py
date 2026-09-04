import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException, status

from app.db.models.session import Session as SessionModel
from app.db.models.summary import Summary as SummaryModel
from app.db.models.patient import Patient as PatientModel
from app.db.models.conversation_turn import ConversationTurn as ConversationTurnModel
from app.db.models.document import Document as DocumentModel
from app.db.models.extracted_entity import ExtractedEntity as ExtractedEntityModel
from app.db.models.audit_log import AuditLog as AuditLogModel

from app.ai.schemas.summary import ClinicalSummarySchema
from app.ai.providers import get_llm_provider
from app.ai.prompts.summary_prompts import build_clinical_summary_prompt_v1, PROMPT_VERSION_V1
from app.core.logging import logger

VALID_WORKFLOW_TRANSITIONS = {
    "NOT_GENERATED": ["GENERATING"],
    "GENERATING": ["GENERATED", "PHYSICIAN_REVIEW", "FAILED"],
    "GENERATED": ["PHYSICIAN_REVIEW", "ACCEPTED", "REJECTED", "GENERATING"],
    "PHYSICIAN_REVIEW": ["ACCEPTED", "REJECTED", "GENERATING", "EDITS_PROPOSED"],
    "EDITS_PROPOSED": ["ACCEPTED", "REJECTED", "GENERATING"],
    "ACCEPTED": [],  # Final state
    "REJECTED": ["REGENERATING", "GENERATING"],
    "REGENERATING": ["GENERATING", "FAILED"],
    "FAILED": ["GENERATING"],
}


class ClinicalSummaryService:
    def __init__(self, provider_type: Optional[str] = None):
        self.llm_provider = get_llm_provider(provider_type)

    def _validate_transition(self, current_status: str, target_status: str):
        allowed = VALID_WORKFLOW_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Invalid workflow state transition from '{current_status}' to '{target_status}'.",
                    "code": "INVALID_WORKFLOW_TRANSITION",
                    "allowed_transitions": allowed,
                },
            )

    def _log_audit_event(
        self,
        db: DBSession,
        session_id: uuid.UUID,
        action: str,
        resource: str = "summary",
        status_code: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        audit_log = AuditLogModel(
            session_id=session_id,
            user_id="physician_system",
            action=action,
            resource=resource,
            status=status_code,
            details=details or {},
            request_id=request_id or "internal-service",
        )
        db.add(audit_log)
        db.commit()

    def generate_summary(
        self,
        session_id: uuid.UUID,
        db: DBSession,
        max_retries: int = 2,
        request_id: Optional[str] = None,
    ) -> SummaryModel:
        # 1. Fetch Session & Patient
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Session with ID '{session_id}' not found.", "code": "SESSION_NOT_FOUND"},
            )

        patient = db.query(PatientModel).filter(PatientModel.id == session.patient_id).first()
        patient_info = (
            f"ID: {patient.id}, Name: {patient.first_name} {patient.last_name}, DOB: {patient.dob}, Gender: {patient.gender}"
            if patient
            else "Not provided"
        )

        # 2. Retrieve existing summary or initialize new record
        summary_record = db.query(SummaryModel).filter(SummaryModel.session_id == session_id).first()
        if not summary_record:
            summary_record = SummaryModel(
                session_id=session_id,
                workflow_status="NOT_GENERATED",
                status="DRAFT",
            )
            db.add(summary_record)
            db.commit()
            db.refresh(summary_record)

        # Validate workflow transition
        self._validate_transition(summary_record.workflow_status, "GENERATING")
        summary_record.workflow_status = "GENERATING"
        db.commit()

        # 3. Gather structured session data
        turns = (
            db.query(ConversationTurnModel)
            .filter(ConversationTurnModel.session_id == session_id)
            .order_by(ConversationTurnModel.turn_index.asc())
            .all()
        )
        conversation_text = "\n".join([f"[{t.speaker}]: {t.content}" for t in turns]) if turns else "No dialogue recorded."

        extracted_entities = (
            db.query(ExtractedEntityModel)
            .filter(ExtractedEntityModel.session_id == session_id)
            .all()
        )
        doc_text = (
            "\n".join([f"- {e.entity_type} ({e.entity_name}): {e.value} (Abnormal: {e.is_abnormal})" for e in extracted_entities])
            if extracted_entities
            else "No document extractions available."
        )

        # Gather safety alerts
        red_flags_list = []
        for t in turns:
            if t.safety_alerts:
                red_flags_list.append(str(t.safety_alerts))
        red_flags_text = "\n".join(red_flags_list) if red_flags_list else "No safety red flags detected."

        # 4. Build prompt
        system_prompt, user_prompt, prompt_ver = build_clinical_summary_prompt_v1(
            session_id=str(session_id),
            patient_demographics=patient_info,
            conversation_turns=conversation_text,
            document_extractions=doc_text,
            safety_red_flags=red_flags_text,
        )

        # 5. Execute Validation + Bounded Retry Pipeline
        validated_summary: Optional[ClinicalSummarySchema] = None
        last_exception: Optional[Exception] = None

        for attempt in range(1, max_retries + 2):
            try:
                logger.info(f"Summary generation attempt {attempt} for session {session_id}")
                retry_prompt = user_prompt
                if attempt > 1 and last_exception:
                    retry_prompt += f"\n\nPREVIOUS ATTEMPT VALIDATION ERROR: {str(last_exception)}. Please correct the schema formatting strictly."

                result = self.llm_provider.generate_structured(
                    prompt=retry_prompt,
                    system_prompt=system_prompt,
                    schema_class=ClinicalSummarySchema,
                )
                validated_summary = result
                break  # Successful generation and validation
            except Exception as exc:
                last_exception = exc
                logger.warning(f"Validation failure on attempt {attempt}: {str(exc)}")

        # 6. Check if validation succeeded
        if not validated_summary:
            summary_record.workflow_status = "FAILED"
            summary_record.generation_error = f"Validation failed after {max_retries + 1} retries: {str(last_exception)}"
            db.commit()

            self._log_audit_event(
                db, session_id, "SUMMARY_GENERATION_FAILED", status_code="FAILURE",
                details={"error": summary_record.generation_error}, request_id=request_id
            )

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Failed to generate valid clinical summary matching schema.",
                    "code": "SUMMARY_GENERATION_FAILED",
                    "details": str(last_exception),
                },
            )

        # 7. Persist Validated Summary
        summary_dict = validated_summary.model_dump()
        summary_record.structured_summary = summary_dict
        summary_record.chief_complaint = summary_dict.get("generated_summary_text")
        summary_record.workflow_status = "PHYSICIAN_REVIEW"
        summary_record.status = "DRAFT"
        summary_record.prompt_version = prompt_ver
        summary_record.llm_model = getattr(self.llm_provider, "__class__", {}).__name__
        summary_record.generation_error = None
        db.commit()

        # Update Session status
        session.status = "SUMMARY_GENERATED"
        db.commit()

        self._log_audit_event(
            db, session_id, "SUMMARY_GENERATED", status_code="SUCCESS",
            details={"version": summary_record.version, "status": "PHYSICIAN_REVIEW"}, request_id=request_id
        )

        return summary_record

    def get_summary(self, session_id: uuid.UUID, db: DBSession) -> SummaryModel:
        summary = db.query(SummaryModel).filter(SummaryModel.session_id == session_id).first()
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Summary for session '{session_id}' not found.", "code": "SUMMARY_NOT_FOUND"},
            )
        return summary

    def edit_summary(
        self,
        session_id: uuid.UUID,
        edited_content: Dict[str, Any],
        db: DBSession,
        physician_id: str = "physician_1",
        request_id: Optional[str] = None,
    ) -> SummaryModel:
        summary = self.get_summary(session_id, db)
        
        # Verify transition
        self._validate_transition(summary.workflow_status, "EDITS_PROPOSED")
        
        # Merge edited fields with existing AI structured summary without overwriting original AI version
        base_summary = summary.physician_edited_summary or summary.structured_summary or {}
        merged_summary = {**base_summary, **edited_content}
        
        # Validate merged dictionary against ClinicalSummarySchema
        try:
            ClinicalSummarySchema.model_validate(merged_summary)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"Physician edited summary violates schema: {str(e)}", "code": "INVALID_SCHEMA_EDIT"},
            )

        summary.physician_edited_summary = merged_summary
        summary.workflow_status = "PHYSICIAN_REVIEW"
        summary.status = "EDITS_PROPOSED"
        db.commit()

        self._log_audit_event(
            db, session_id, "SUMMARY_EDITED", status_code="SUCCESS",
            details={"edited_by": physician_id}, request_id=request_id
        )

        return summary

    def accept_summary(
        self,
        session_id: uuid.UUID,
        physician_notes: Optional[str],
        db: DBSession,
        physician_id: str = "physician_1",
        request_id: Optional[str] = None,
    ) -> SummaryModel:
        summary = self.get_summary(session_id, db)
        
        self._validate_transition(summary.workflow_status, "ACCEPTED")
        
        summary.workflow_status = "ACCEPTED"
        summary.status = "ACCEPTED"
        summary.physician_notes = physician_notes
        summary.accepted_at = datetime.now(timezone.utc)
        summary.accepted_by = physician_id
        db.commit()

        # Update session status
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            session.status = "PHYSICIAN_REVIEWED"
            db.commit()

        self._log_audit_event(
            db, session_id, "SUMMARY_ACCEPTED", status_code="SUCCESS",
            details={"accepted_by": physician_id, "accepted_at": summary.accepted_at.isoformat()},
            request_id=request_id
        )

        return summary

    def reject_summary(
        self,
        session_id: uuid.UUID,
        reason: str,
        db: DBSession,
        physician_id: str = "physician_1",
        request_id: Optional[str] = None,
    ) -> SummaryModel:
        summary = self.get_summary(session_id, db)
        
        self._validate_transition(summary.workflow_status, "REJECTED")
        
        summary.workflow_status = "REJECTED"
        summary.status = "REJECTED"
        summary.rejected_at = datetime.now(timezone.utc)
        summary.rejected_reason = reason
        db.commit()

        self._log_audit_event(
            db, session_id, "SUMMARY_REJECTED", status_code="SUCCESS",
            details={"rejected_by": physician_id, "reason": reason},
            request_id=request_id
        )

        return summary
