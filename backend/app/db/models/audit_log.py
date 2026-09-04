import uuid
from sqlalchemy import String, ForeignKey, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # SUCCESS, FAILURE, FORBIDDEN
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    request_id: Mapped[str] = mapped_column(String(100), nullable=True)
