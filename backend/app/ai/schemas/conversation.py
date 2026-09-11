"""Conversation module output schemas."""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class SectionEnum(str, Enum):
    """Valid interview sections."""
    IDENTIFICATION = "IDENTIFICATION"
    CHIEF_COMPLAINT = "CHIEF_COMPLAINT"
    HPI = "HPI"
    PAST_MEDICAL_HISTORY = "PAST_MEDICAL_HISTORY"
    PAST_SURGICAL_HISTORY = "PAST_SURGICAL_HISTORY"
    MEDICATIONS = "MEDICATIONS"
    ALLERGIES = "ALLERGIES"
    FAMILY_HISTORY = "FAMILY_HISTORY"
    PERSONAL_HISTORY = "PERSONAL_HISTORY"
    REVIEW_OF_SYSTEMS = "REVIEW_OF_SYSTEMS"
    COMPLETED = "COMPLETED"


class ConversationResponseSchema(BaseModel):
    """Schema for LLM responses in conversation module.
    
    Captures AI-generated questions/responses with confidence and state tracking.
    """
    
    response: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="AI-generated response or question for the patient"
    )
    
    confidence: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) of response appropriateness"
    )
    
    next_section: str = Field(
        default="HPI",
        description="Next interview section to advance to after response"
    )
    
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted clinical data from user response"
    )
    
    safety_alert: Optional[str] = Field(
        None,
        description="Safety alert if red flag detected"
    )
    
    requires_physician_review: bool = Field(
        default=False,
        description="Whether response requires immediate physician review"
    )
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is a valid probability."""
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0 and 1")
        return round(v, 3)
    
    @field_validator("next_section")
    @classmethod
    def validate_next_section(cls, v: str) -> str:
        """Ensure next section is valid."""
        valid_sections = [s.value for s in SectionEnum]
        if v not in valid_sections:
            raise ValueError(f"Invalid section: {v}. Valid sections: {valid_sections}")
        return v
    
    @field_validator("response")
    @classmethod
    def validate_response(cls, v: str) -> str:
        """Ensure response is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError("Response cannot be empty")
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "Thank you for that information. You mentioned chest pain. Can you describe the exact location of the pain?",
                "confidence": 0.97,
                "next_section": "HPI",
                "extracted_data": {"symptom": "chest pain", "onset": "2 hours ago"},
                "safety_alert": None,
                "requires_physician_review": False
            }
        }
    }
