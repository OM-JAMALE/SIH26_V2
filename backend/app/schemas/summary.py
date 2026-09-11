"""Pydantic v2 schemas for Summary model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class ClinicalSummaryContent(BaseModel):
    """Schema for clinical summary content."""
    
    chief_complaint: Optional[str] = Field(None, description="Chief complaint")
    hpi: Optional[str] = Field(None, description="History of present illness")
    pmh: Optional[str] = Field(None, description="Past medical history")
    psh: Optional[str] = Field(None, description="Past surgical history")
    drug_and_allergy: Optional[str] = Field(None, description="Medications and allergies")
    family_history: Optional[str] = Field(None, description="Family history")
    personal_history: Optional[str] = Field(None, description="Personal/social history")
    ros: Optional[str] = Field(None, description="Review of systems")
    prior_investigations: Optional[str] = Field(None, description="Prior investigations/lab results")
    
    key_findings: List[str] = Field(default_factory=list, description="Key clinical findings")
    red_flags: List[str] = Field(default_factory=list, description="Red flags requiring escalation")
    recommendations: List[str] = Field(default_factory=list, description="Clinical recommendations")
    uncertainty_notes: str = Field("", description="Explicit uncertainty representation")


class SummaryBase(BaseModel):
    """Base schema for Summary."""
    
    version: int = Field(1, ge=1, description="Summary version")
    llm_model: str = Field("mock-llm", description="LLM model used")
    prompt_version: str = Field("clinical_summary_v1", description="Prompt version")


class SummaryCreate(SummaryBase):
    """Schema for creating a summary."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")


class SummaryUpdate(BaseModel):
    """Schema for updating a summary."""
    
    workflow_status: Optional[str] = None
    structured_summary: Optional[ClinicalSummaryContent] = None
    physician_edited_summary: Optional[ClinicalSummaryContent] = None
    physician_notes: Optional[str] = None


class SummaryResponse(SummaryBase):
    """Schema for summary response."""
    
    id: uuid.UUID = Field(..., description="Summary ID")
    session_id: uuid.UUID = Field(..., description="Session ID")
    version: int = Field(..., description="Summary version")
    workflow_status: str = Field(..., description="Workflow status")
    status: str = Field(..., description="Legacy status field")
    
    structured_summary: Optional[ClinicalSummaryContent] = Field(None, description="AI-generated summary")
    physician_edited_summary: Optional[ClinicalSummaryContent] = Field(None, description="Physician-edited summary")
    
    physician_notes: Optional[str] = Field(None, description="Physician's notes")
    generation_error: Optional[str] = Field(None, description="Generation error if any")
    
    accepted_at: Optional[datetime] = Field(None, description="Acceptance timestamp")
    accepted_by: Optional[str] = Field(None, description="Accepted by user/physician")
    rejected_at: Optional[datetime] = Field(None, description="Rejection timestamp")
    rejected_reason: Optional[str] = Field(None, description="Rejection reason")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SummaryListResponse(BaseModel):
    """Schema for list of summaries."""
    
    total: int = Field(..., description="Total number of summaries")
    items: List[SummaryResponse] = Field(..., description="List of summaries")


class SummaryGenerateRequest(BaseModel):
    """Schema for requesting summary generation."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")
    include_documents: bool = Field(True, description="Include document data in summary")


class SummaryPhysicianReviewRequest(BaseModel):
    """Schema for physician review."""
    
    action: str = Field(..., description="Action: ACCEPT, REJECT, EDIT")
    notes: Optional[str] = Field(None, description="Physician notes")
    edited_summary: Optional[ClinicalSummaryContent] = Field(None, description="Edited summary if action=EDIT")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if action=REJECT")


class RedFlagAlert(BaseModel):
    """Schema for red flag alerts."""
    
    flag_type: str = Field(..., description="Type of red flag")
    description: str = Field(..., description="Flag description")
    severity: str = Field(..., description="Severity: LOW, MEDIUM, HIGH, CRITICAL")
    recommended_action: str = Field(..., description="Recommended action")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert timestamp")
