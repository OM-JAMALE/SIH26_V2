"""Document module output schemas."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DocumentTypeEnum(str, Enum):
    """Supported document types."""
    LAB_REPORT = "LAB_REPORT"
    IMAGING_REPORT = "IMAGING_REPORT"
    PRESCRIPTION = "PRESCRIPTION"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    CLINICAL_NOTE = "CLINICAL_NOTE"
    UNKNOWN = "UNKNOWN"


class EntityTypeEnum(str, Enum):
    """Supported extracted entity types."""
    LAB_RESULT = "LAB_RESULT"
    VITAL_SIGN = "VITAL_SIGN"
    MEDICATION = "MEDICATION"
    DIAGNOSIS = "DIAGNOSIS"
    PROCEDURE = "PROCEDURE"
    ALLERGY = "ALLERGY"
    IMAGING_FINDING = "IMAGING_FINDING"
    OTHER = "OTHER"


class TableSchema(BaseModel):
    """Extracted table data."""
    
    title: Optional[str] = Field(
        None,
        description="Table title or header"
    )
    
    headers: List[str] = Field(
        default_factory=list,
        description="Column headers"
    )
    
    rows: List[List[str]] = Field(
        default_factory=list,
        description="Table data rows"
    )
    
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in table extraction"
    )


class ExtractedEntity(BaseModel):
    """Extracted clinical entity."""
    
    entity_type: EntityTypeEnum = Field(
        ...,
        description="Type of extracted entity"
    )
    
    entity_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Name or description of entity"
    )
    
    value: str = Field(
        ...,
        description="Entity value as string"
    )
    
    numeric_value: Optional[float] = Field(
        None,
        description="Numeric value if applicable"
    )
    
    unit: Optional[str] = Field(
        None,
        description="Unit of measurement if applicable"
    )
    
    reference_range: Optional[str] = Field(
        None,
        description="Reference range for lab results"
    )
    
    is_abnormal: bool = Field(
        default=False,
        description="Whether value is abnormal (deterministic detection)"
    )
    
    confidence_score: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Extraction confidence (0-1)"
    )
    
    metadata_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    @field_validator("entity_name")
    @classmethod
    def validate_entity_name(cls, v: str) -> str:
        """Ensure entity name is not empty."""
        if not v or not v.strip():
            raise ValueError("Entity name cannot be empty")
        return v.strip()
    
    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str) -> str:
        """Ensure value is not empty."""
        if not v or not v.strip():
            raise ValueError("Value cannot be empty")
        return v.strip()


class DocumentExtractionSchema(BaseModel):
    """Schema for document extraction output.
    
    Captures extracted text, tables, and entities from uploaded documents.
    """
    
    document_type: DocumentTypeEnum = Field(
        default=DocumentTypeEnum.UNKNOWN,
        description="Type of document"
    )
    
    extracted_text: str = Field(
        default="",
        description="Full extracted text from document"
    )
    
    tables: List[TableSchema] = Field(
        default_factory=list,
        description="Extracted tables from document"
    )
    
    entities: List[ExtractedEntity] = Field(
        default_factory=list,
        description="Extracted clinical entities"
    )
    
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Overall extraction confidence (0-1)"
    )
    
    summary_notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Summary of extracted information"
    )
    
    information_gaps: List[str] = Field(
        default_factory=list,
        description="Missing or unclear information"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about extraction quality or content"
    )
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is a valid probability."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0 and 1")
        return round(v, 3)
    
    @field_validator("tables")
    @classmethod
    def validate_tables(cls, v: List[TableSchema]) -> List[TableSchema]:
        """Ensure tables are valid."""
        for table in v:
            if not table.headers and not table.rows:
                raise ValueError("Table must have headers or rows")
        return v
    
    @property
    def abnormal_entities(self) -> List[ExtractedEntity]:
        """Get only abnormal entities."""
        return [e for e in self.entities if e.is_abnormal]
    
    @property
    def lab_results(self) -> List[ExtractedEntity]:
        """Get only lab result entities."""
        return [e for e in self.entities if e.entity_type == EntityTypeEnum.LAB_RESULT]
    
    @property
    def medications(self) -> List[ExtractedEntity]:
        """Get only medication entities."""
        return [e for e in self.entities if e.entity_type == EntityTypeEnum.MEDICATION]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "document_type": "LAB_REPORT",
                "extracted_text": "Blood test performed on 2024-01-15...",
                "tables": [
                    {
                        "title": "Biochemistry Panel",
                        "headers": ["Test", "Value", "Unit", "Range"],
                        "rows": [["Glucose", "145", "mg/dL", "70-99"]],
                        "confidence": 0.95
                    }
                ],
                "entities": [
                    {
                        "entity_type": "LAB_RESULT",
                        "entity_name": "Fasting Blood Sugar",
                        "value": "145 mg/dL",
                        "numeric_value": 145.0,
                        "unit": "mg/dL",
                        "reference_range": "70-99",
                        "is_abnormal": True,
                        "confidence_score": 0.99
                    }
                ],
                "confidence": 0.92,
                "summary_notes": "Elevated glucose detected"
            }
        }
    }
