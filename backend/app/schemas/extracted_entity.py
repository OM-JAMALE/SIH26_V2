"""Pydantic v2 schemas for ExtractedEntity model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class ExtractedEntityBase(BaseModel):
    """Base schema for ExtractedEntity."""
    
    entity_type: str = Field(..., description="Entity type: LAB_RESULT, MEDICATION, DIAGNOSIS, VITAL, SYMPTOM")
    entity_name: str = Field(..., min_length=1, max_length=200, description="Entity name")
    value: str = Field(..., min_length=1, max_length=255, description="Entity value")
    numeric_value: Optional[float] = Field(None, description="Numeric value if applicable")
    unit: Optional[str] = Field(None, max_length=50, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, max_length=100, description="Reference range")
    is_abnormal: bool = Field(False, description="Whether value is abnormal")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score (0-1)")
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("entity_type")
    def validate_entity_type(cls, v):
        """Validate entity type."""
        valid_types = ["LAB_RESULT", "MEDICATION", "DIAGNOSIS", "VITAL", "SYMPTOM"]
        if v.upper() not in valid_types:
            raise ValueError(f"Entity type must be one of {valid_types}")
        return v.upper()


class ExtractedEntityCreate(ExtractedEntityBase):
    """Schema for creating an extracted entity."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")
    document_id: Optional[uuid.UUID] = Field(None, description="Document ID if from document")


class ExtractedEntityResponse(ExtractedEntityBase):
    """Schema for extracted entity response."""
    
    id: uuid.UUID = Field(..., description="Entity ID")
    session_id: uuid.UUID = Field(..., description="Session ID")
    document_id: Optional[uuid.UUID] = Field(None, description="Document ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ExtractedEntityListResponse(BaseModel):
    """Schema for list of extracted entities."""
    
    total: int = Field(..., description="Total number of entities")
    items: List[ExtractedEntityResponse] = Field(..., description="List of entities")


class LabAbnormalitySchema(BaseModel):
    """Schema for lab abnormality detection (deterministic)."""
    
    test_name: str = Field(..., description="Lab test name")
    value: float = Field(..., description="Test value")
    normal_range: str = Field(..., description="Normal range (e.g., '70-100')")
    is_abnormal: bool = Field(..., description="Whether abnormal")
    severity: str = Field(..., description="Severity: LOW, MEDIUM, HIGH")

    @field_validator("severity")
    def validate_severity(cls, v):
        """Validate severity."""
        valid_severities = ["LOW", "MEDIUM", "HIGH"]
        if v.upper() not in valid_severities:
            raise ValueError(f"Severity must be one of {valid_severities}")
        return v.upper()


def detect_lab_abnormality(test_name: str, value: float, reference_range: str) -> LabAbnormalitySchema:
    """
    Deterministic lab abnormality detection (NOT LLM-based).
    
    Rules are hardcoded and inspectable per healthcare safety requirements.
    """
    severity = "LOW"
    is_abnormal = False
    
    # Common lab tests with hardcoded rules
    common_tests = {
        "hemoglobin": {"min": 12.0, "max": 17.0, "unit": "g/dL"},
        "wbc": {"min": 4.5, "max": 11.0, "unit": "K/uL"},
        "glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
        "creatinine": {"min": 0.7, "max": 1.3, "unit": "mg/dL"},
        "sodium": {"min": 136, "max": 145, "unit": "mEq/L"},
        "potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L"},
    }
    
    test_lower = test_name.lower().strip()
    
    if test_lower in common_tests:
        rules = common_tests[test_lower]
        min_val = rules["min"]
        max_val = rules["max"]
        
        if value < min_val or value > max_val:
            is_abnormal = True
            # Determine severity based on deviation
            if value < min_val:
                percent_below = ((min_val - value) / min_val) * 100
            else:
                percent_above = ((value - max_val) / max_val) * 100
                percent_below = percent_above
            
            if percent_below > 30:
                severity = "HIGH"
            elif percent_below > 15:
                severity = "MEDIUM"
            else:
                severity = "LOW"
    
    return LabAbnormalitySchema(
        test_name=test_name,
        value=value,
        normal_range=reference_range or f"{common_tests.get(test_lower, {}).get('min', 'N/A')}-{common_tests.get(test_lower, {}).get('max', 'N/A')}",
        is_abnormal=is_abnormal,
        severity=severity,
    )
