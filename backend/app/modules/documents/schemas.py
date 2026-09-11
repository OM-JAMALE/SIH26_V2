import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


EntityType = Literal["LAB_RESULT", "MEDICATION", "DIAGNOSIS", "VITAL", "SYMPTOM"]


class EntityItemSchema(BaseModel):
    """Pydantic model for an individual extracted entity candidate from document."""
    entity_type: EntityType = Field(..., description="Classification of clinical entity")
    entity_name: str = Field(..., description="Name of test, medication, symptom, diagnosis, or vital")
    value: str = Field(..., description="Raw text value as written in document")
    numeric_value: Optional[float] = Field(None, description="Extracted numerical reading if applicable")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g. mg/dL, g/dL, mmHg)")
    reference_range: Optional[str] = Field(None, description="Normal reference range if printed in document")
    is_abnormal: bool = Field(False, description="Flagged abnormal deterministically")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Extraction confidence score")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Additional contextual metadata")


class DocumentExtractionSchema(BaseModel):
    """Structured extraction output requested from LLM/multimodal parser for Module B."""
    document_type: str = Field(default="LAB_REPORT", description="Inferred document type (LAB_REPORT, PRESCRIPTION, DISCHARGE_SUMMARY)")
    entities: List[EntityItemSchema] = Field(default_factory=list, description="Extracted entities")
    summary_notes: Optional[str] = Field(None, description="High-level factual document notes without diagnostic speculation")


class ExtractedEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    document_id: Optional[uuid.UUID]
    entity_type: str
    entity_name: str
    value: str
    numeric_value: Optional[float]
    unit: Optional[str]
    reference_range: Optional[str]
    is_abnormal: bool
    confidence_score: float
    metadata_json: Dict[str, Any]
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    filename: str
    mime_type: str
    file_size: int
    processing_status: str
    raw_text: Optional[str]
    created_at: datetime
    extracted_entities: List[ExtractedEntityResponse] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    documents: List[DocumentUploadResponse]
    total: int


class EntityListResponse(BaseModel):
    entities: List[ExtractedEntityResponse]
    total: int
    abnormal_count: int


class DocumentDeleteResponse(BaseModel):
    success: bool
    message: str
    document_id: uuid.UUID
