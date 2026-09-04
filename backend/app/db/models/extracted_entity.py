import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Float, Boolean, ForeignKey, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.session import Session
    from app.db.models.document import Document


class ExtractedEntity(Base, TimestampMixin):
    __tablename__ = "extracted_entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Entity Type: LAB_RESULT, MEDICATION, DIAGNOSIS, VITAL, SYMPTOM
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    numeric_value: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=True)
    reference_range: Mapped[str] = mapped_column(String(100), nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="extracted_entities")
    document: Mapped["Document"] = relationship("Document", back_populates="extracted_entities")
