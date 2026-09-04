import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Integer, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.session import Session
    from app.db.models.extracted_entity import ExtractedEntity


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Processing Status: PENDING, EXTRACTED, FAILED
    processing_status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="documents")
    extracted_entities: Mapped[List["ExtractedEntity"]] = relationship("ExtractedEntity", back_populates="document", cascade="all, delete-orphan")
