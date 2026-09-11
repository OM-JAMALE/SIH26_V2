"""Clinical Summary repository for summary management operations."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import Summary
from app.db.repositories.base import BaseRepository


class SummaryRepository(BaseRepository[Summary]):
    """Repository for Summary model."""

    def __init__(self, db: Session):
        """Initialize summary repository.
        
        Args:
            db: Database session
        """
        super().__init__(Summary, db)

    def create_summary(
        self,
        session_id: UUID,
        version: int = 1,
        workflow_status: str = "NOT_GENERATED",
        llm_model: str = "mock-llm",
        prompt_version: str = "clinical_summary_v1"
    ) -> Summary:
        """Create a new clinical summary.
        
        Args:
            session_id: Session UUID
            version: Summary version (incremented on regeneration)
            workflow_status: NOT_GENERATED, GENERATING, GENERATED, etc.
            llm_model: LLM model used
            prompt_version: Prompt version for reproducibility
            
        Returns:
            Created Summary instance
        """
        return self.create(
            session_id=session_id,
            version=version,
            workflow_status=workflow_status,
            status="DRAFT",
            llm_model=llm_model,
            prompt_version=prompt_version
        )

    def get_summary(self, summary_id: UUID) -> Optional[Summary]:
        """Get summary by ID.
        
        Args:
            summary_id: Summary UUID
            
        Returns:
            Summary instance or None
        """
        return self.get(summary_id)

    def get_summaries_by_session(self, session_id: UUID) -> List[Summary]:
        """Get all summaries for a session (ordered by version descending).
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of Summary instances
        """
        return self.db.query(Summary).filter(
            Summary.session_id == session_id
        ).order_by(desc(Summary.version)).all()

    def get_latest_summary(self, session_id: UUID) -> Optional[Summary]:
        """Get latest (highest version) summary for session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Summary instance or None
        """
        return self.db.query(Summary).filter(
            Summary.session_id == session_id
        ).order_by(desc(Summary.version)).first()

    def list_by_conversation(self, session_id: UUID) -> List[Summary]:
        """Get all summaries for a conversation/session.
        
        Alias for get_summaries_by_session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            List of Summary instances
        """
        return self.get_summaries_by_session(session_id)

    def get_summaries_by_workflow_status(
        self,
        workflow_status: str
    ) -> List[Summary]:
        """Get summaries with specific workflow status.
        
        Args:
            workflow_status: NOT_GENERATED, GENERATING, GENERATED, PHYSICIAN_REVIEW, ACCEPTED, REJECTED
            
        Returns:
            List of Summary instances
        """
        return self.filter(workflow_status=workflow_status)

    def get_generated_summaries(self) -> List[Summary]:
        """Get all generated summaries (awaiting review).
        
        Returns:
            List of generated Summary instances
        """
        return self.db.query(Summary).filter(
            Summary.workflow_status == "GENERATED"
        ).all()

    def get_pending_physician_review(self) -> List[Summary]:
        """Get summaries pending physician review.
        
        Returns:
            List of Summary instances in PHYSICIAN_REVIEW status
        """
        return self.filter(workflow_status="PHYSICIAN_REVIEW")

    def get_accepted_summaries(self) -> List[Summary]:
        """Get all physician-accepted summaries.
        
        Returns:
            List of accepted Summary instances
        """
        return self.filter(workflow_status="ACCEPTED")

    def update_summary_content(
        self,
        summary_id: UUID,
        chief_complaint: Optional[str] = None,
        hpi: Optional[str] = None,
        pmh: Optional[str] = None,
        drug_and_allergy: Optional[str] = None,
        family_history: Optional[str] = None,
        personal_history: Optional[str] = None,
        ros: Optional[str] = None,
        prior_investigations: Optional[str] = None,
        structured_summary: Optional[dict] = None
    ) -> Optional[Summary]:
        """Update summary content fields.
        
        Args:
            summary_id: Summary UUID
            chief_complaint: Chief complaint text (optional)
            hpi: History of present illness (optional)
            pmh: Past medical history (optional)
            drug_and_allergy: Medications and allergies (optional)
            family_history: Family history (optional)
            personal_history: Personal/social history (optional)
            ros: Review of systems (optional)
            prior_investigations: Prior investigations (optional)
            structured_summary: Structured summary JSON (optional)
            
        Returns:
            Updated Summary instance or None
        """
        update_dict = {}
        if chief_complaint is not None:
            update_dict["chief_complaint"] = chief_complaint
        if hpi is not None:
            update_dict["hpi"] = hpi
        if pmh is not None:
            update_dict["pmh"] = pmh
        if drug_and_allergy is not None:
            update_dict["drug_and_allergy"] = drug_and_allergy
        if family_history is not None:
            update_dict["family_history"] = family_history
        if personal_history is not None:
            update_dict["personal_history"] = personal_history
        if ros is not None:
            update_dict["ros"] = ros
        if prior_investigations is not None:
            update_dict["prior_investigations"] = prior_investigations
        if structured_summary is not None:
            update_dict["structured_summary"] = structured_summary
        
        return self.update(summary_id, **update_dict)

    def update_workflow_status(
        self,
        summary_id: UUID,
        workflow_status: str
    ) -> Optional[Summary]:
        """Update workflow status.
        
        Args:
            summary_id: Summary UUID
            workflow_status: New workflow status
            
        Returns:
            Updated Summary instance or None
        """
        return self.update(summary_id, workflow_status=workflow_status)

    def mark_generating(self, summary_id: UUID) -> Optional[Summary]:
        """Mark summary as generating (in progress).
        
        Args:
            summary_id: Summary UUID
            
        Returns:
            Updated Summary instance or None
        """
        return self.update_workflow_status(summary_id, "GENERATING")

    def mark_generated(self, summary_id: UUID) -> Optional[Summary]:
        """Mark summary as generated (ready for review).
        
        Args:
            summary_id: Summary UUID
            
        Returns:
            Updated Summary instance or None
        """
        return self.update_workflow_status(summary_id, "GENERATED")

    def mark_physician_review(self, summary_id: UUID) -> Optional[Summary]:
        """Mark summary as pending physician review.
        
        Args:
            summary_id: Summary UUID
            
        Returns:
            Updated Summary instance or None
        """
        return self.update_workflow_status(summary_id, "PHYSICIAN_REVIEW")

    def accept_summary(
        self,
        summary_id: UUID,
        accepted_by: str
    ) -> Optional[Summary]:
        """Accept summary (physician approval).
        
        Args:
            summary_id: Summary UUID
            accepted_by: Physician/user who accepted
            
        Returns:
            Updated Summary instance or None
        """
        from datetime import datetime, timezone
        return self.update(
            summary_id,
            workflow_status="ACCEPTED",
            status="PUBLISHED",
            accepted_at=datetime.now(timezone.utc),
            accepted_by=accepted_by
        )

    def reject_summary(
        self,
        summary_id: UUID,
        rejection_reason: str
    ) -> Optional[Summary]:
        """Reject summary (physician rejection).
        
        Args:
            summary_id: Summary UUID
            rejection_reason: Reason for rejection
            
        Returns:
            Updated Summary instance or None
        """
        from datetime import datetime, timezone
        return self.update(
            summary_id,
            workflow_status="REJECTED",
            rejected_at=datetime.now(timezone.utc),
            rejected_reason=rejection_reason
        )

    def set_generation_error(
        self,
        summary_id: UUID,
        error: str
    ) -> Optional[Summary]:
        """Record generation error.
        
        Args:
            summary_id: Summary UUID
            error: Error message
            
        Returns:
            Updated Summary instance or None
        """
        return self.update(
            summary_id,
            workflow_status="FAILED",
            generation_error=error
        )

    def add_physician_notes(
        self,
        summary_id: UUID,
        notes: str
    ) -> Optional[Summary]:
        """Add/update physician notes.
        
        Args:
            summary_id: Summary UUID
            notes: Physician notes
            
        Returns:
            Updated Summary instance or None
        """
        return self.update(summary_id, physician_notes=notes)

    def set_physician_edited(
        self,
        summary_id: UUID,
        edited_summary: dict
    ) -> Optional[Summary]:
        """Store physician-edited summary.
        
        Args:
            summary_id: Summary UUID
            edited_summary: Edited summary dictionary
            
        Returns:
            Updated Summary instance or None
        """
        return self.update(summary_id, physician_edited_summary=edited_summary)

    def delete_summary(self, summary_id: UUID) -> bool:
        """Delete summary.
        
        Args:
            summary_id: Summary UUID
            
        Returns:
            True if deleted
        """
        return self.delete(summary_id)

    def summary_exists(self, summary_id: UUID) -> bool:
        """Check if summary exists.
        
        Args:
            summary_id: Summary UUID
            
        Returns:
            True if exists
        """
        return self.exists(id=summary_id)

    def count_summaries_by_session(self, session_id: UUID) -> int:
        """Count summaries for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Number of summaries
        """
        return self.count(session_id=session_id)

    def get_summary_stats(self, session_id: UUID) -> dict:
        """Get summary statistics for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Dictionary with summary statistics
        """
        summaries = self.get_summaries_by_session(session_id)
        if not summaries:
            return {"session_id": str(session_id), "total_count": 0}
        
        generated = [s for s in summaries if s.workflow_status in ["GENERATED", "ACCEPTED", "REJECTED"]]
        accepted = [s for s in summaries if s.workflow_status == "ACCEPTED"]
        rejected = [s for s in summaries if s.workflow_status == "REJECTED"]
        
        return {
            "session_id": str(session_id),
            "total_count": len(summaries),
            "generated_count": len(generated),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "latest_version": max((s.version for s in summaries), default=0),
            "latest_status": summaries[0].workflow_status if summaries else None
        }
