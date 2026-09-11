"""AI output schemas for structured validation.

This module provides Pydantic schemas for all AI-generated outputs:
- Conversation responses
- Document extraction
- Clinical summaries
- Lab abnormality detection
- Red flag detection (deterministic)

All schemas include validation rules and are designed for production use.
Red flag detection is DETERMINISTIC (not LLM-based) for patient safety.
"""

# From summary module
from app.ai.schemas.summary import (
    ClinicalSummarySchema,
    ClinicalItem,
    MedicationItem,
    LabInvestigation,
    RedFlagItem,
    InformationStatus,
)

# From conversation module
from app.ai.schemas.conversation import (
    ConversationResponseSchema,
    SectionEnum,
)

# From document module
from app.ai.schemas.document import (
    DocumentExtractionSchema,
    DocumentTypeEnum,
    EntityTypeEnum,
    TableSchema,
    ExtractedEntity,
)

# From lab module
from app.ai.schemas.lab import (
    LabAbnormalitySchema,
    ClinicalAbnormalitySchema,
    SeverityEnum,
)

# From red flags module
from app.ai.schemas.red_flags import (
    RedFlagDetector,
    RedFlag,
    RedFlagSeverity,
    RedFlagCategory,
)

__all__ = [
    # Summary schemas
    "ClinicalSummarySchema",
    "ClinicalItem",
    "MedicationItem",
    "LabInvestigation",
    "RedFlagItem",
    "InformationStatus",
    
    # Conversation schemas
    "ConversationResponseSchema",
    "SectionEnum",
    
    # Document schemas
    "DocumentExtractionSchema",
    "DocumentTypeEnum",
    "EntityTypeEnum",
    "TableSchema",
    "ExtractedEntity",
    
    # Lab schemas
    "LabAbnormalitySchema",
    "ClinicalAbnormalitySchema",
    "SeverityEnum",
    
    # Red flags (deterministic)
    "RedFlagDetector",
    "RedFlag",
    "RedFlagSeverity",
    "RedFlagCategory",
]
