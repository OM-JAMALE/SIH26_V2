import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.session import Session
    from app.db.models.patient import Patient


class Consent(Base, TimestampMixin):
    __tablename__ = "consents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    terms_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    signature_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="consents")
    patient: Mapped["Patient"] = relationship("Patient", back_populates="consents")
