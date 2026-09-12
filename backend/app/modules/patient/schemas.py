from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PatientCreateRequest(BaseModel):
    first_name: str = Field(..., json_schema_extra={"example": "Rajesh"})
    last_name: str = Field(..., json_schema_extra={"example": "Kumar"})
    dob: str = Field(..., description="ISO format YYYY-MM-DD", json_schema_extra={"example": "1985-06-15"})
    gender: str = Field(..., description="Male, Female, Other", json_schema_extra={"example": "Male"})
    national_health_id: Optional[str] = Field(None, description="ABHA / National Health ID", json_schema_extra={"example": "91-1234-5678-9012"})
    contact_number: Optional[str] = Field(None, json_schema_extra={"example": "+91-9876543210"})


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    national_health_id: Optional[str] = None
    first_name: str
    last_name: str
    dob: str
    gender: str
    contact_number: Optional[str] = None
    created_at: Optional[datetime] = None


class PatientSessionSummaryItem(BaseModel):
    session_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    mode: str
    status: str
    lifecycle_status: str
    current_section: str
    chief_complaint: Optional[str] = None
    safety_status: str
    turn_count: int = 0
    document_count: int = 0
    summary_status: Optional[str] = None
    summary_id: Optional[str] = None


class DoctorPatientSearchResult(BaseModel):
    id: str
    national_health_id: Optional[str] = None
    first_name: str
    last_name: str
    dob: str
    gender: str
    contact_number: Optional[str] = None
    session_count: int = 0
    last_session_at: Optional[datetime] = None


class DoctorPatientFullHistory(BaseModel):
    patient: PatientResponse
    sessions: List[PatientSessionSummaryItem]
    total_sessions: int
    total_documents: int
