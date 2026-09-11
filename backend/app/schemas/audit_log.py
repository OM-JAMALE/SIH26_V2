"""Pydantic v2 schemas for AuditLog model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class AuditLogBase(BaseModel):
    """Base schema for AuditLog."""
    
    action: str = Field(..., min_length=1, max_length=100, description="Action performed")
    resource: str = Field(..., min_length=1, max_length=100, description="Resource type")
    status: str = Field(..., description="Status: SUCCESS, FAILURE, FORBIDDEN")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit log."""
    
    session_id: Optional[uuid.UUID] = Field(None, description="Session ID if applicable")
    user_id: Optional[str] = Field(None, description="User ID")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response."""
    
    id: uuid.UUID = Field(..., description="Audit log ID")
    session_id: Optional[uuid.UUID] = Field(None, description="Session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    request_id: Optional[str] = Field(None, description="Request ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema for list of audit logs."""
    
    total: int = Field(..., description="Total number of audit logs")
    items: List[AuditLogResponse] = Field(..., description="List of audit logs")


class AuditLogFilterRequest(BaseModel):
    """Schema for filtering audit logs."""
    
    session_id: Optional[uuid.UUID] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AuditTrailReport(BaseModel):
    """Schema for audit trail report."""
    
    session_id: Optional[uuid.UUID] = Field(None, description="Session ID")
    patient_id: Optional[uuid.UUID] = Field(None, description="Patient ID")
    total_actions: int = Field(..., description="Total actions in trail")
    success_count: int = Field(..., description="Successful actions")
    failure_count: int = Field(..., description="Failed actions")
    forbidden_count: int = Field(..., description="Forbidden actions")
    timeline: List[AuditLogResponse] = Field(..., description="Chronological audit log")
    report_generated_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation time")


class SensitiveActionLog(BaseModel):
    """Schema for logging sensitive operations."""
    
    action: str = Field(..., description="Sensitive action")
    resource_type: str = Field(..., description="Type of resource (e.g., PATIENT_DATA, CONSENT, EXPORT)")
    resource_id: Optional[uuid.UUID] = Field(None, description="Resource ID")
    actor: str = Field(..., description="Who performed the action")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="IP address of actor")
    result: str = Field(..., description="Result: SUCCESS, FAILURE, DENIED")
    notes: Optional[str] = Field(None, description="Additional notes (no PII/clinical data)")

    # Never log:
    # - Patient clinical content
    # - API keys or auth tokens
    # - Sensitive personal information
    # - File contents
