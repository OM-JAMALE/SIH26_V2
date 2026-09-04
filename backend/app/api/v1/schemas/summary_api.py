from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EditSummaryRequest(BaseModel):
    edited_summary: Dict[str, Any] = Field(..., description="Partial or full structured summary edits")


class AcceptSummaryRequest(BaseModel):
    physician_notes: Optional[str] = Field(None, description="Optional notes provided by reviewing physician")
    physician_id: Optional[str] = Field("physician_1", description="Physician identifier")


class RejectSummaryRequest(BaseModel):
    reason: str = Field(..., description="Reason for rejection or request for regeneration")
    physician_id: Optional[str] = Field("physician_1", description="Physician identifier")


class SummaryResponse(BaseModel):
    id: str
    session_id: str
    version: int
    workflow_status: str
    status: str
    structured_summary: Optional[Dict[str, Any]] = None
    physician_edited_summary: Optional[Dict[str, Any]] = None
    active_summary: Dict[str, Any] = Field(..., description="Returns physician_edited_summary if present, else structured_summary")
    llm_model: str
    prompt_version: str
    generation_error: Optional[str] = None
    physician_notes: Optional[str] = None
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
