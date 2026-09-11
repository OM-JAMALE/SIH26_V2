"""Database repositories for Health AI.

Repositories provide data access layer with CRUD operations and query methods.
Each repository is model-specific and handles its own business logic queries.

All repositories use SQLAlchemy ORM and session management from app.db.session.

Repositories:
- BaseRepository: Common CRUD operations
- PatientRepository: Patient data operations
- SessionRepository: Conversation/session management
- ConversationTurnRepository: Conversation turn operations
- DocumentRepository: Document management
- ExtractedEntityRepository: Entity management
- SummaryRepository: Clinical summary operations
- ConsentRepository: Consent/privacy audit trail
- AuditLogRepository: Security/compliance logging
"""

from app.db.repositories.base import BaseRepository
from app.db.repositories.patient import PatientRepository
from app.db.repositories.session import SessionRepository
from app.db.repositories.conversation_turn import ConversationTurnRepository
from app.db.repositories.document import DocumentRepository
from app.db.repositories.extracted_entity import ExtractedEntityRepository
from app.db.repositories.summary import SummaryRepository
from app.db.repositories.consent import ConsentRepository
from app.db.repositories.audit_log import AuditLogRepository

__all__ = [
    "BaseRepository",
    "PatientRepository",
    "SessionRepository",
    "ConversationTurnRepository",
    "DocumentRepository",
    "ExtractedEntityRepository",
    "SummaryRepository",
    "ConsentRepository",
    "AuditLogRepository",
]
