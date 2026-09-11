"""Session (Conversation) repository for conversation-related operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import Session as SessionModel, ConversationTurn
from app.db.repositories.base import BaseRepository


class SessionRepository(BaseRepository[SessionModel]):
    """Repository for Session (Conversation) model."""

    def __init__(self, db: Session):
        """Initialize session repository.
        
        Args:
            db: Database session
        """
        super().__init__(SessionModel, db)

    def create_session(
        self,
        patient_id: UUID,
        mode: str = "MODERN",
        status: str = "INITIATED",
        lifecycle_status: str = "CREATED",
        current_section: str = "CHIEF_COMPLAINT"
    ) -> SessionModel:
        """Create a new consultation session.
        
        Args:
            patient_id: Patient UUID
            mode: Session mode (MODERN or AYUSH)
            status: Overall status
            lifecycle_status: Lifecycle status
            current_section: Current conversation section
            
        Returns:
            Created Session instance
        """
        return self.create(
            patient_id=patient_id,
            mode=mode,
            status=status,
            lifecycle_status=lifecycle_status,
            current_section=current_section,
            session_metadata={},
            structured_history={},
            safety_status="SAFE",
            safety_alerts={}
        )

    def get_session(self, session_id: UUID) -> Optional[SessionModel]:
        """Get session by ID.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Session instance or None
        """
        return self.get(session_id)

    def get_session_with_turns(self, session_id: UUID) -> Optional[SessionModel]:
        """Get session with eager-loaded conversation turns.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Session instance with turns or None
        """
        return self.db.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()

    def get_sessions_by_patient(self, patient_id: UUID) -> List[SessionModel]:
        """Get all sessions for a patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            List of Session instances
        """
        return self.filter(patient_id=patient_id)

    def get_active_session(self, patient_id: UUID) -> Optional[SessionModel]:
        """Get most recent active session for patient.
        
        Args:
            patient_id: Patient UUID
            
        Returns:
            Session instance or None
        """
        return self.db.query(SessionModel).filter(
            SessionModel.patient_id == patient_id,
            SessionModel.lifecycle_status.in_(["CREATED", "IN_PROGRESS"])
        ).order_by(desc(SessionModel.created_at)).first()

    def update_section(
        self,
        session_id: UUID,
        current_section: str,
        socrates_state: Optional[str] = None
    ) -> Optional[SessionModel]:
        """Update conversation section (advance state machine).
        
        Args:
            session_id: Session UUID
            current_section: New section
            socrates_state: SOCRATES sub-state if applicable
            
        Returns:
            Updated Session instance or None
        """
        update_dict = {"current_section": current_section}
        if socrates_state:
            update_dict["socrates_state"] = socrates_state
        return self.update(session_id, **update_dict)

    def update_structured_history(
        self,
        session_id: UUID,
        history: dict
    ) -> Optional[SessionModel]:
        """Update accumulated clinical history.
        
        Args:
            session_id: Session UUID
            history: Structured history dictionary
            
        Returns:
            Updated Session instance or None
        """
        return self.update(session_id, structured_history=history)

    def update_safety_status(
        self,
        session_id: UUID,
        safety_status: str,
        safety_alerts: Optional[dict] = None
    ) -> Optional[SessionModel]:
        """Update safety status and alerts.
        
        Args:
            session_id: Session UUID
            safety_status: SAFE, WARNING, or ESCALATED
            safety_alerts: Optional alerts dictionary
            
        Returns:
            Updated Session instance or None
        """
        update_dict = {"safety_status": safety_status}
        if safety_alerts is not None:
            update_dict["safety_alerts"] = safety_alerts
        return self.update(session_id, **update_dict)

    def acknowledge_disclaimer(self, session_id: UUID) -> Optional[SessionModel]:
        """Mark disclaimer as acknowledged.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Updated Session instance or None
        """
        from datetime import datetime, timezone
        return self.update(
            session_id,
            disclaimer_acknowledged=True,
            disclaimer_acknowledged_at=datetime.now(timezone.utc)
        )

    def update_lifecycle_status(
        self,
        session_id: UUID,
        lifecycle_status: str
    ) -> Optional[SessionModel]:
        """Update lifecycle status.
        
        Args:
            session_id: Session UUID
            lifecycle_status: CREATED, IN_PROGRESS, SAFETY_ESCALATED, COMPLETED
            
        Returns:
            Updated Session instance or None
        """
        return self.update(session_id, lifecycle_status=lifecycle_status)

    def update_overall_status(
        self,
        session_id: UUID,
        status: str
    ) -> Optional[SessionModel]:
        """Update overall status.
        
        Args:
            session_id: Session UUID
            status: INITIATED, IN_CONVERSATION, DOCUMENTS_UPLOADED, etc.
            
        Returns:
            Updated Session instance or None
        """
        return self.update(session_id, status=status)

    def get_all_turns(self, session_id: UUID) -> List[ConversationTurn]:
        """Get all conversation turns for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of ConversationTurn instances
        """
        return self.db.query(ConversationTurn).filter(
            ConversationTurn.session_id == session_id
        ).order_by(ConversationTurn.turn_index).all()

    def get_turn_count(self, session_id: UUID) -> int:
        """Get number of turns in session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Number of turns
        """
        return self.db.query(ConversationTurn).filter(
            ConversationTurn.session_id == session_id
        ).count()

    def get_turns_by_section(self, session_id: UUID, section: str) -> List[ConversationTurn]:
        """Get conversation turns for a specific section.
        
        Args:
            session_id: Session UUID
            section: Conversation section
            
        Returns:
            List of ConversationTurn instances
        """
        return self.db.query(ConversationTurn).filter(
            ConversationTurn.session_id == session_id,
            ConversationTurn.section == section
        ).order_by(ConversationTurn.turn_index).all()

    def complete_session(self, session_id: UUID) -> Optional[SessionModel]:
        """Mark session as completed.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Updated Session instance or None
        """
        return self.update(
            session_id,
            lifecycle_status="COMPLETED",
            status="COMPLETED"
        )

    def delete_session(self, session_id: UUID) -> bool:
        """Delete session (cascades to turns, documents, summaries, etc.).
        
        Args:
            session_id: Session UUID
            
        Returns:
            True if deleted
        """
        return self.delete(session_id)

    def session_exists(self, session_id: UUID) -> bool:
        """Check if session exists.
        
        Args:
            session_id: Session UUID
            
        Returns:
            True if exists
        """
        return self.exists(id=session_id)
