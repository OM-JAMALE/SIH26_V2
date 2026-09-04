import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException, status

from app.db.models.session import Session as SessionModel
from app.db.models.patient import Patient as PatientModel
from app.db.models.conversation_turn import ConversationTurn as ConversationTurnModel
from app.db.models.audit_log import AuditLog as AuditLogModel

from app.modules.conversation.schemas import (
    SessionMode,
    SessionLifecycle,
    InterviewState,
    SocratesAttribute,
    ClinicalHistory,
    StructuredExtraction,
    SafetyAlertPayload,
    ProcessResponseResult,
    SessionStateResponse,
)
from app.modules.conversation.state_machine import InterviewStateMachine, update_clinical_history
from app.modules.conversation.questions import (
    get_template_question,
    INITIAL_DISCLAIMER_TEXT,
    DETERMINISTIC_EMERGENCY_MESSAGE,
    NO_DIAGNOSIS_TREATMENT_ADVICE_RESPONSE,
)
from app.modules.conversation.safety import SafetyRulesEngine
from app.modules.conversation.extraction import get_extraction_provider
from app.core.logging import logger


class ClinicalConversationService:
    def __init__(self, provider_type: Optional[str] = None):
        self.state_machine = InterviewStateMachine()
        self.safety_engine = SafetyRulesEngine()
        self.extraction_provider = get_extraction_provider(provider_type)

    def _log_audit_event(
        self,
        db: DBSession,
        session_id: uuid.UUID,
        action: str,
        resource: str = "conversation_session",
        status_code: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        audit_log = AuditLogModel(
            session_id=session_id,
            user_id="patient_session",
            action=action,
            resource=resource,
            status=status_code,
            details=details or {},
            request_id=request_id or "conversation-service",
        )
        db.add(audit_log)
        db.commit()

    def create_session(
        self,
        patient_id: uuid.UUID,
        mode: SessionMode = SessionMode.MODERN,
        disclaimer_acknowledged: bool = False,
        db: DBSession = None,
        request_id: Optional[str] = None,
    ) -> SessionModel:
        # Verify patient exists or auto-create default patient record
        patient = db.query(PatientModel).filter(PatientModel.id == patient_id).first()
        if not patient:
            patient = PatientModel(
                id=patient_id,
                first_name="Rajesh",
                last_name="Kumar",
                dob="1985-06-15",
                gender="Male",
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        now = datetime.now(timezone.utc)
        session = SessionModel(
            patient_id=patient_id,
            lifecycle_status="IN_PROGRESS" if disclaimer_acknowledged else "CREATED",
            status="INITIATED",
            mode=mode.value,
            disclaimer_acknowledged=disclaimer_acknowledged,
            disclaimer_acknowledged_at=now if disclaimer_acknowledged else None,
            current_section=InterviewState.IDENTIFICATION.value,
            socrates_state=SocratesAttribute.SITE.value,
            structured_history=ClinicalHistory().model_dump(),
            safety_status="SAFE",
            safety_alerts={},
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        self._log_audit_event(
            db, session.id, "SESSION_CREATED", details={"mode": mode.value, "acknowledged": disclaimer_acknowledged}, request_id=request_id
        )
        if disclaimer_acknowledged:
            self._log_audit_event(
                db, session.id, "DISCLAIMER_ACKNOWLEDGED", details={"acknowledged_at": now.isoformat()}, request_id=request_id
            )

        # Create initial system greeting turn
        initial_question = get_template_question(InterviewState.IDENTIFICATION, mode=mode)
        turn = ConversationTurnModel(
            session_id=session.id,
            turn_index=1,
            speaker="SYSTEM",
            content=initial_question,
            extracted_data={},
            safety_alerts={},
            section=InterviewState.IDENTIFICATION.value,
        )
        db.add(turn)
        db.commit()

        return session

    def acknowledge_disclaimer(
        self, session_id: uuid.UUID, db: DBSession, request_id: Optional[str] = None
    ) -> SessionModel:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Session '{session_id}' not found.", "code": "SESSION_NOT_FOUND"},
            )

        now = datetime.now(timezone.utc)
        session.disclaimer_acknowledged = True
        session.disclaimer_acknowledged_at = now
        if session.lifecycle_status == "CREATED":
            session.lifecycle_status = "IN_PROGRESS"
        db.commit()

        self._log_audit_event(
            db, session_id, "DISCLAIMER_ACKNOWLEDGED", details={"acknowledged_at": now.isoformat()}, request_id=request_id
        )
        return session

    def get_session_state(self, session_id: uuid.UUID, db: DBSession) -> SessionStateResponse:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Session '{session_id}' not found.", "code": "SESSION_NOT_FOUND"},
            )

        # Fetch latest system question
        latest_turn = (
            db.query(ConversationTurnModel)
            .filter(ConversationTurnModel.session_id == session_id, ConversationTurnModel.speaker == "SYSTEM")
            .order_by(ConversationTurnModel.turn_index.desc())
            .first()
        )
        latest_question = latest_turn.content if latest_turn else INITIAL_DISCLAIMER_TEXT

        history_obj = ClinicalHistory.model_validate(session.structured_history or {})
        safety_obj = SafetyAlertPayload.model_validate(session.safety_alerts or {"flagged": False})

        return SessionStateResponse(
            session_id=str(session.id),
            patient_id=str(session.patient_id),
            lifecycle_status=SessionLifecycle(session.lifecycle_status),
            mode=SessionMode(session.mode),
            disclaimer_acknowledged=session.disclaimer_acknowledged,
            disclaimer_acknowledged_at=session.disclaimer_acknowledged_at,
            current_section=InterviewState(session.current_section),
            socrates_state=SocratesAttribute(session.socrates_state) if session.socrates_state else None,
            latest_question=latest_question,
            structured_history=history_obj,
            safety=safety_obj,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def submit_patient_response(
        self,
        session_id: uuid.UUID,
        raw_text: str,
        db: DBSession,
        request_id: Optional[str] = None,
    ) -> ProcessResponseResult:
        # 1. Fetch Session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"Session '{session_id}' not found.", "code": "SESSION_NOT_FOUND"},
            )

        # 2. Check Disclaimer Acknowledgment
        if not session.disclaimer_acknowledged:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Interview disclaimer must be acknowledged before submitting responses.",
                    "code": "DISCLAIMER_NOT_ACKNOWLEDGED",
                    "disclaimer": INITIAL_DISCLAIMER_TEXT,
                },
            )

        # 3. Check Session Lifecycle Status
        if session.lifecycle_status in ["COMPLETED", "SAFETY_ESCALATED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Session '{session_id}' is in lifecycle state '{session.lifecycle_status}' and cannot accept further responses.",
                    "code": "SESSION_NOT_IN_PROGRESS",
                },
            )

        # 4. Record Immutable Patient Turn
        turn_count = db.query(ConversationTurnModel).filter(ConversationTurnModel.session_id == session_id).count()
        patient_turn = ConversationTurnModel(
            session_id=session_id,
            turn_index=turn_count + 1,
            speaker="PATIENT",
            content=raw_text,
            extracted_data={},
            safety_alerts={},
            section=session.current_section,
        )
        db.add(patient_turn)
        db.commit()

        self._log_audit_event(
            db, session_id, "PATIENT_RESPONSE_RECEIVED", details={"turn_index": patient_turn.turn_index}, request_id=request_id
        )

        # 5. Perform Extraction
        extraction = self.extraction_provider.extract(
            text=raw_text,
            current_section=session.current_section,
            socrates_state=session.socrates_state or "SITE",
        )
        patient_turn.extracted_data = extraction.model_dump()
        db.commit()

        self._log_audit_event(db, session_id, "CLINICAL_EXTRACTION_COMPLETED", request_id=request_id)

        # 6. Update Structured History
        history_obj = ClinicalHistory.model_validate(session.structured_history or {})
        history_obj = update_clinical_history(history_obj, extraction)
        session.structured_history = history_obj.model_dump()
        db.commit()

        # 7. Evaluate Deterministic Red-Flag Safety Rules
        safety_eval = self.safety_engine.evaluate_safety(raw_text, extraction)
        if safety_eval.flagged:
            session.safety_status = "ESCALATED"
            session.lifecycle_status = "SAFETY_ESCALATED"
            session.safety_alerts = safety_eval.model_dump()
            db.commit()

            # Record emergency system turn
            sys_turn = ConversationTurnModel(
                session_id=session_id,
                turn_index=turn_count + 2,
                speaker="SYSTEM",
                content=DETERMINISTIC_EMERGENCY_MESSAGE,
                extracted_data={},
                safety_alerts=safety_eval.model_dump(),
                section=session.current_section,
            )
            db.add(sys_turn)
            db.commit()

            self._log_audit_event(
                db, session_id, "SAFETY_RULE_TRIGGERED", status_code="CRITICAL",
                details={"rule_id": safety_eval.rule_id}, request_id=request_id
            )
            self._log_audit_event(
                db, session_id, "SAFETY_ESCALATED", status_code="CRITICAL", request_id=request_id
            )

            return ProcessResponseResult(
                session_id=str(session_id),
                lifecycle_status=SessionLifecycle.SAFETY_ESCALATED,
                current_section=InterviewState(session.current_section),
                socrates_state=SocratesAttribute(session.socrates_state) if session.socrates_state else None,
                next_question=DETERMINISTIC_EMERGENCY_MESSAGE,
                structured_updates=extraction.model_dump(),
                safety=safety_eval,
            )

        # 8. Deterministic State Machine Transition
        curr_state = InterviewState(session.current_section)
        curr_soc = SocratesAttribute(session.socrates_state) if session.socrates_state else None
        
        next_state, next_soc, next_lifecycle = self.state_machine.advance_state(
            current_state=curr_state,
            current_socrates=curr_soc,
            history=history_obj,
            extraction=extraction,
        )

        session.current_section = next_state.value
        session.socrates_state = next_soc.value if next_soc else None
        session.lifecycle_status = next_lifecycle.value
        if next_lifecycle == SessionLifecycle.COMPLETED:
            session.status = "IN_CONVERSATION"
        db.commit()

        self._log_audit_event(
            db, session_id, "STATE_TRANSITION",
            details={"from": curr_state.value, "to": next_state.value, "socrates": next_soc.value if next_soc else None},
            request_id=request_id
        )

        if next_lifecycle == SessionLifecycle.COMPLETED:
            self._log_audit_event(db, session_id, "SESSION_COMPLETED", request_id=request_id)

        # 9. Get Next Template Question
        primary_symptom = history_obj.chief_complaint[0].symptom if history_obj.chief_complaint else "symptom"
        next_q = get_template_question(
            state=next_state,
            socrates_attr=next_soc,
            mode=SessionMode(session.mode),
            symptom_name=primary_symptom,
        )

        # Append boundary message if patient asked for diagnosis/treatment
        if extraction.patient_inquired_diagnosis_or_treatment:
            next_q = f"{NO_DIAGNOSIS_TREATMENT_ADVICE_RESPONSE}\n\n{next_q}"

        # Record System Question Turn
        sys_turn = ConversationTurnModel(
            session_id=session_id,
            turn_index=turn_count + 2,
            speaker="SYSTEM",
            content=next_q,
            extracted_data={},
            safety_alerts={},
            section=next_state.value,
        )
        db.add(sys_turn)
        db.commit()

        return ProcessResponseResult(
            session_id=str(session_id),
            lifecycle_status=next_lifecycle,
            current_section=next_state,
            socrates_state=next_soc,
            next_question=next_q,
            structured_updates=extraction.model_dump(),
            safety=SafetyAlertPayload(flagged=False),
        )

    def get_conversation_history(self, session_id: uuid.UUID, db: DBSession) -> List[ConversationTurnModel]:
        turns = (
            db.query(ConversationTurnModel)
            .filter(ConversationTurnModel.session_id == session_id)
            .order_by(ConversationTurnModel.turn_index.asc())
            .all()
        )
        return turns
