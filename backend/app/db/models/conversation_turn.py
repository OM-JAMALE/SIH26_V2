import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, JSON, Integer, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.session import Session


class ConversationTurn(Base, TimestampMixin):
    __tablename__ = "conversation_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # PATIENT or SYSTEM
    speaker: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    extracted_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    safety_alerts: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    section: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="conversation_turns")
