"""Pydantic v2 schemas for ConversationTurn model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class ConversationTurnBase(BaseModel):
    """Base schema for ConversationTurn."""
    
    speaker: str = Field(..., description="Who spoke: PATIENT or SYSTEM")
    content: str = Field(..., min_length=1, description="Turn content/message")
    section: str = Field(..., description="Section of the conversation")
    extracted_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extracted structured data")
    safety_alerts: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Safety alerts for this turn")

    @field_validator("speaker")
    def validate_speaker(cls, v):
        """Validate speaker."""
        valid_speakers = ["PATIENT", "SYSTEM"]
        if v.upper() not in valid_speakers:
            raise ValueError(f"Speaker must be one of {valid_speakers}")
        return v.upper()

    @field_validator("section")
    def validate_section(cls, v):
        """Validate section."""
        valid_sections = [
            "CHIEF_COMPLAINT", "HPI", "SOCRATES", "PMH", "PSH",
            "DRUG_HISTORY", "ALLERGY_HISTORY", "FAMILY_HISTORY",
            "PERSONAL_HISTORY", "ROS", "COMPLETED"
        ]
        if v.upper() not in valid_sections:
            raise ValueError(f"Section must be one of {valid_sections}")
        return v.upper()


class ConversationTurnCreate(ConversationTurnBase):
    """Schema for creating a conversation turn."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")


class ConversationTurnResponse(ConversationTurnBase):
    """Schema for conversation turn response."""
    
    id: uuid.UUID = Field(..., description="Turn ID")
    session_id: uuid.UUID = Field(..., description="Session ID")
    turn_index: int = Field(..., description="Turn index in conversation")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ConversationTurnListResponse(BaseModel):
    """Schema for list of conversation turns."""
    
    total: int = Field(..., description="Total number of turns")
    items: List[ConversationTurnResponse] = Field(..., description="List of turns")


class ConversationTurnMessageRequest(BaseModel):
    """Schema for sending a message in conversation."""
    
    user_input: str = Field(..., min_length=1, max_length=5000, description="User message")
    section: Optional[str] = Field(None, description="Specify section if advancing")


class ConversationTurnMessageResponse(BaseModel):
    """Schema for message response."""
    
    user_turn: ConversationTurnResponse = Field(..., description="User's turn")
    system_turn: ConversationTurnResponse = Field(..., description="System's response turn")
    next_section: str = Field(..., description="Next section to move to")
    can_advance: bool = Field(..., description="Whether can advance to next section")
    safety_flags: Dict[str, Any] = Field(default_factory=dict, description="Any safety flags")
