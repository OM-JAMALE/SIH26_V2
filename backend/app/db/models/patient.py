import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Date, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.session import Session
    from app.db.models.consent import Consent


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    national_health_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[str] = mapped_column(String(20), nullable=False)  # ISO Date string YYYY-MM-DD
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(50), nullable=True)

    # Relationships
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="patient", cascade="all, delete-orphan")
    consents: Mapped[List["Consent"]] = relationship("Consent", back_populates="patient", cascade="all, delete-orphan")
