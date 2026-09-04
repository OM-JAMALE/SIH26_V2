import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.patient import Patient
    from app.db.models.conversation_turn import ConversationTurn
    from app.db.models.document import Document
    from app.db.models.extracted_entity import ExtractedEntity
    from app.db.models.summary import Summary
    from app.db.models.consent import Consent


class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
    # Session Lifecycle Status: CREATED, IN_PROGRESS, SAFETY_ESCALATED, COMPLETED
    lifecycle_status: Mapped[str] = mapped_column(String(50), default="CREATED", nullable=False, index=True)
    
    # Legacy / Overall Workflow Status: INITIATED, IN_CONVERSATION, DOCUMENTS_UPLOADED, SUMMARY_GENERATED, PHYSICIAN_REVIEWED, CONSENTED, COMPLETED
    status: Mapped[str] = mapped_column(String(50), default="INITIATED", nullable=False, index=True)
    
    # Mode: MODERN vs AYUSH
    mode: Mapped[str] = mapped_column(String(20), default="MODERN", nullable=False)
    
    # Disclaimer Acknowledgment
    disclaimer_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disclaimer_acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Current clinical history section & SOCRATES state
    current_section: Mapped[str] = mapped_column(String(50), default="CHIEF_COMPLAINT", nullable=False)
    socrates_state: Mapped[str] = mapped_column(String(50), default="SITE", nullable=True)
    
    # Accumulated Structured Clinical History (JSON)
    structured_history: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    # Safety Engine State (SAFE, WARNING, ESCALATED)
    safety_status: Mapped[str] = mapped_column(String(50), default="SAFE", nullable=False)
    safety_alerts: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    session_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="sessions")
    conversation_turns: Mapped[List["ConversationTurn"]] = relationship("ConversationTurn", back_populates="session", cascade="all, delete-orphan")
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    extracted_entities: Mapped[List["ExtractedEntity"]] = relationship("ExtractedEntity", back_populates="session", cascade="all, delete-orphan")
    summaries: Mapped[List["Summary"]] = relationship("Summary", back_populates="session", cascade="all, delete-orphan")
    consents: Mapped[List["Consent"]] = relationship("Consent", back_populates="session", cascade="all, delete-orphan")
