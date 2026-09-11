"""
Pydantic v2 Schemas for Health AI Platform.

This package contains all request/response validation schemas using Pydantic v2.
Schemas are used at API boundaries to validate and document data models.

Never expose ORM models directly - always use schemas.

Modules:
- patient.py - Patient data schemas
- session.py - Conversation session schemas
- conversation_turn.py - Individual conversation turn schemas
- document.py - Document upload/management schemas
- extracted_entity.py - Extracted lab/clinical entity schemas
- summary.py - Clinical summary generation schemas
- consent.py - Consent/privacy audit schemas
- audit_log.py - Audit logging schemas
"""

from app.schemas.patient import (
    PatientBase,
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse,
)
from app.schemas.session import (
    SessionBase,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionDetailResponse,
)
from app.schemas.conversation_turn import (
    ConversationTurnBase,
    ConversationTurnCreate,
    ConversationTurnResponse,
    ConversationTurnListResponse,
    ConversationTurnMessageRequest,
    ConversationTurnMessageResponse,
)
from app.schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from app.schemas.extracted_entity import (
    ExtractedEntityBase,
    ExtractedEntityCreate,
    ExtractedEntityResponse,
    ExtractedEntityListResponse,
    LabAbnormalitySchema,
    detect_lab_abnormality,
)
from app.schemas.summary import (
    ClinicalSummaryContent,
    SummaryBase,
    SummaryCreate,
    SummaryUpdate,
    SummaryResponse,
    SummaryListResponse,
    SummaryGenerateRequest,
    SummaryPhysicianReviewRequest,
    RedFlagAlert,
)
from app.schemas.consent import (
    ConsentBase,
    ConsentCreate,
    ConsentUpdate,
    ConsentResponse,
    ConsentListResponse,
    ConsentAuditTrail,
    ConsentHistoryResponse,
    ConsentPurposes,
    ConsentRequest,
)
from app.schemas.audit_log import (
    AuditLogBase,
    AuditLogCreate,
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogFilterRequest,
    AuditTrailReport,
    SensitiveActionLog,
)

__all__ = [
    # Patient schemas
    "PatientBase",
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "PatientListResponse",
    
    # Session schemas
    "SessionBase",
    "SessionCreate",
    "SessionUpdate",
    "SessionResponse",
    "SessionDetailResponse",
    
    # Conversation turn schemas
    "ConversationTurnBase",
    "ConversationTurnCreate",
    "ConversationTurnResponse",
    "ConversationTurnListResponse",
    "ConversationTurnMessageRequest",
    "ConversationTurnMessageResponse",
    
    # Document schemas
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentUploadRequest",
    "DocumentUploadResponse",
    
    # Extracted entity schemas
    "ExtractedEntityBase",
    "ExtractedEntityCreate",
    "ExtractedEntityResponse",
    "ExtractedEntityListResponse",
    "LabAbnormalitySchema",
    "detect_lab_abnormality",
    
    # Summary schemas
    "ClinicalSummaryContent",
    "SummaryBase",
    "SummaryCreate",
    "SummaryUpdate",
    "SummaryResponse",
    "SummaryListResponse",
    "SummaryGenerateRequest",
    "SummaryPhysicianReviewRequest",
    "RedFlagAlert",
    
    # Consent schemas
    "ConsentBase",
    "ConsentCreate",
    "ConsentUpdate",
    "ConsentResponse",
    "ConsentListResponse",
    "ConsentAuditTrail",
    "ConsentHistoryResponse",
    "ConsentPurposes",
    "ConsentRequest",
    
    # Audit log schemas
    "AuditLogBase",
    "AuditLogCreate",
    "AuditLogResponse",
    "AuditLogListResponse",
    "AuditLogFilterRequest",
    "AuditTrailReport",
    "SensitiveActionLog",
]
