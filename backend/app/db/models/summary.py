import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.session import Session


class Summary(Base, TimestampMixin):
    __tablename__ = "summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Workflow Status: NOT_GENERATED, GENERATING, GENERATED, PHYSICIAN_REVIEW, ACCEPTED, REJECTED, REGENERATING, FAILED
    workflow_status: Mapped[str] = mapped_column(String(50), default="NOT_GENERATED", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False)  # Legacy compatibility

    # Raw / Structured LLM Generated Output
    structured_summary: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Physician Edited Output (Preserves distinction between AI generated and Physician edited)
    physician_edited_summary: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    chief_complaint: Mapped[str] = mapped_column(Text, nullable=True)
    hpi: Mapped[str] = mapped_column(Text, nullable=True)
    pmh: Mapped[str] = mapped_column(Text, nullable=True)
    drug_and_allergy: Mapped[str] = mapped_column(Text, nullable=True)
    family_history: Mapped[str] = mapped_column(Text, nullable=True)
    personal_history: Mapped[str] = mapped_column(Text, nullable=True)
    ros: Mapped[str] = mapped_column(Text, nullable=True)
    prior_investigations: Mapped[str] = mapped_column(Text, nullable=True)
    
    physician_notes: Mapped[str] = mapped_column(Text, nullable=True)
    llm_model: Mapped[str] = mapped_column(String(100), default="mock-llm", nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), default="clinical_summary_v1", nullable=False)
    generation_error: Mapped[str] = mapped_column(Text, nullable=True)

    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by: Mapped[str] = mapped_column(String(100), nullable=True)
    rejected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_reason: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="summaries")
