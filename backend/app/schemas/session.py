"""Pydantic v2 schemas for Session (Conversation) model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class SessionBase(BaseModel):
    """Base schema for Session/Conversation."""
    
    mode: str = Field("MODERN", description="Session mode: MODERN or AYUSH")
    
    @field_validator("mode")
    def validate_mode(cls, v):
        """Validate mode."""
        valid_modes = ["MODERN", "AYUSH"]
        if v.upper() not in valid_modes:
            raise ValueError(f"Mode must be one of {valid_modes}")
        return v.upper()


class SessionCreate(SessionBase):
    """Schema for creating a new session."""
    
    patient_id: uuid.UUID = Field(..., description="Patient ID")


class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    
    lifecycle_status: Optional[str] = None
    status: Optional[str] = None
    current_section: Optional[str] = None
    socrates_state: Optional[str] = None
    structured_history: Optional[Dict[str, Any]] = None
    safety_status: Optional[str] = None
    safety_alerts: Optional[Dict[str, Any]] = None
    disclaimer_acknowledged: Optional[bool] = None


class SessionResponse(SessionBase):
    """Schema for session response."""
    
    id: uuid.UUID = Field(..., description="Session ID")
    patient_id: uuid.UUID = Field(..., description="Patient ID")
    lifecycle_status: str = Field(..., description="Lifecycle status")
    status: str = Field(..., description="Overall status")
    current_section: str = Field(..., description="Current section in conversation")
    socrates_state: Optional[str] = Field(None, description="SOCRATES state")
    safety_status: str = Field(..., description="Safety status")
    safety_alerts: Dict[str, Any] = Field(default_factory=dict, description="Safety alerts")
    disclaimer_acknowledged: bool = Field(..., description="Whether disclaimer was acknowledged")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    """Detailed session response with conversation turns."""
    
    # Note: ConversationTurnResponse must be imported at runtime to avoid circular imports
    conversation_turns: List[dict] = Field(default_factory=list, description="List of conversation turns (serialized)")
    turn_count: int = Field(0, description="Total number of turns")
