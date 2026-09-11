"""Conversation turn repository for turn-related operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import ConversationTurn
from app.db.repositories.base import BaseRepository


class ConversationTurnRepository(BaseRepository[ConversationTurn]):
    """Repository for ConversationTurn model."""

    def __init__(self, db: Session):
        """Initialize conversation turn repository.
        
        Args:
            db: Database session
        """
        super().__init__(ConversationTurn, db)

    def create_turn(
        self,
        session_id: UUID,
        speaker: str,
        content: str,
        section: str,
        turn_index: int,
        extracted_data: Optional[dict] = None,
        safety_alerts: Optional[dict] = None
    ) -> ConversationTurn:
        """Create a new conversation turn.
        
        Args:
            session_id: Session UUID
            speaker: PATIENT or SYSTEM
            content: Turn content/message
            section: Conversation section
            turn_index: Index in turn sequence
            extracted_data: Extracted structured data
            safety_alerts: Any safety alerts
            
        Returns:
            Created ConversationTurn instance
        """
        return self.create(
            session_id=session_id,
            speaker=speaker,
            content=content,
            section=section,
            turn_index=turn_index,
            extracted_data=extracted_data or {},
            safety_alerts=safety_alerts or {}
        )

    def get_turn(self, turn_id: UUID) -> Optional[ConversationTurn]:
        """Get turn by ID.
        
        Args:
            turn_id: Turn UUID
            
        Returns:
            ConversationTurn instance or None
        """
        return self.get(turn_id)

    def get_turns_by_session(self, session_id: UUID) -> List[ConversationTurn]:
        """Get all turns for a session (ordered by turn index).
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of ConversationTurn instances
        """
        return self.db.query(ConversationTurn).filter(
            ConversationTurn.session_id == session_id
        ).order_by(ConversationTurn.turn_index).all()

    def get_latest_turn(self, session_id: UUID) -> Optional[ConversationTurn]:
        """Get latest (most recent) turn in session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            ConversationTurn instance or None
        """
        return self.db.query(ConversationTurn).filter(
            ConversationTurn.session_id == session_id
        ).order_by(desc(ConversationTurn.turn_index)).first()

    def get_turns_by_section(
        self,
        session_id: UUID,
        section: str
    ) -> List[ConversationTurn]:
        """Get all turns for a specific section.
        
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

    def get_turns_by_speaker(
        self,
        session_id: UUID,
        speaker: str
    ) -> List[ConversationTurn]:
        """Get all turns by specific speaker (PATIENT or SYSTEM).
        
        Args:
            session_id: Session UUID
            speaker: PATIENT or SYSTEM
            
        Returns:
            List of ConversationTurn instances
        """
        return self.db.query(ConversationTurn).filter(
            ConversationTurn.session_id == session_id,
            ConversationTurn.speaker == speaker
        ).order_by(ConversationTurn.turn_index).all()

    def get_next_turn_index(self, session_id: UUID) -> int:
        """Get next turn index for session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Next turn index (last index + 1, or 1 if no turns)
        """
        latest = self.get_latest_turn(session_id)
        return 1 if latest is None else latest.turn_index + 1

    def update_turn(
        self,
        turn_id: UUID,
        **kwargs
    ) -> Optional[ConversationTurn]:
        """Update turn information.
        
        Args:
            turn_id: Turn UUID
            **kwargs: Fields to update (content, extracted_data, safety_alerts, etc.)
            
        Returns:
            Updated ConversationTurn instance or None
        """
        return self.update(turn_id, **kwargs)

    def update_extracted_data(
        self,
        turn_id: UUID,
        extracted_data: dict
    ) -> Optional[ConversationTurn]:
        """Update extracted data for turn.
        
        Args:
            turn_id: Turn UUID
            extracted_data: Extracted data dictionary
            
        Returns:
            Updated ConversationTurn instance or None
        """
        return self.update(turn_id, extracted_data=extracted_data)

    def add_safety_alerts(
        self,
        turn_id: UUID,
        alerts: dict
    ) -> Optional[ConversationTurn]:
        """Add safety alerts to turn.
        
        Args:
            turn_id: Turn UUID
            alerts: Safety alerts dictionary
            
        Returns:
            Updated ConversationTurn instance or None
        """
        turn = self.get(turn_id)
        if not turn:
            return None
        
        # Merge with existing alerts
        existing_alerts = turn.safety_alerts or {}
        merged_alerts = {**existing_alerts, **alerts}
        return self.update(turn_id, safety_alerts=merged_alerts)

    def delete_turn(self, turn_id: UUID) -> bool:
        """Delete turn.
        
        Args:
            turn_id: Turn UUID
            
        Returns:
            True if deleted
        """
        return self.delete(turn_id)

    def delete_turns_by_session(self, session_id: UUID) -> int:
        """Delete all turns for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Number of deleted turns
        """
        return self.delete_all(session_id=session_id)

    def turn_exists(self, turn_id: UUID) -> bool:
        """Check if turn exists.
        
        Args:
            turn_id: Turn UUID
            
        Returns:
            True if exists
        """
        return self.exists(id=turn_id)

    def get_turn_count_by_section(self, session_id: UUID, section: str) -> int:
        """Get number of turns in a section.
        
        Args:
            session_id: Session UUID
            section: Conversation section
            
        Returns:
            Number of turns
        """
        return self.db.query(ConversationTurn).filter(
            ConversationTurn.session_id == session_id,
            ConversationTurn.section == section
        ).count()

    def get_section_summary(self, session_id: UUID, section: str) -> dict:
        """Get summary of turns in a section (count, first/last timestamps).
        
        Args:
            session_id: Session UUID
            section: Conversation section
            
        Returns:
            Dictionary with section summary
        """
        turns = self.get_turns_by_section(session_id, section)
        if not turns:
            return {"section": section, "turn_count": 0}
        
        return {
            "section": section,
            "turn_count": len(turns),
            "first_turn_at": turns[0].created_at,
            "last_turn_at": turns[-1].created_at,
            "patient_messages": len([t for t in turns if t.speaker == "PATIENT"]),
            "system_messages": len([t for t in turns if t.speaker == "SYSTEM"])
        }
