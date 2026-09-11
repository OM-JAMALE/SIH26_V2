"""Pydantic v2 schemas for Consent model."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import uuid


class ConsentBase(BaseModel):
    """Base schema for Consent."""
    
    purpose: str = Field(..., min_length=1, max_length=255, description="Purpose of consent")
    granted: bool = Field(True, description="Whether consent is granted")
    terms_version: str = Field("v1.0", description="Terms version")
    ip_address: Optional[str] = Field(None, max_length=50, description="IP address of consent")


class ConsentCreate(ConsentBase):
    """Schema for creating consent record."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")
    patient_id: uuid.UUID = Field(..., description="Patient ID")
    signature_hash: Optional[str] = Field(None, description="Hash of signature")


class ConsentUpdate(BaseModel):
    """Schema for updating consent."""
    
    granted: Optional[bool] = None
    purpose: Optional[str] = None


class ConsentResponse(ConsentBase):
    """Schema for consent response."""
    
    id: uuid.UUID = Field(..., description="Consent ID")
    session_id: uuid.UUID = Field(..., description="Session ID")
    patient_id: uuid.UUID = Field(..., description="Patient ID")
    signature_hash: Optional[str] = Field(None, description="Signature hash")
    granted_at: Optional[datetime] = Field(None, description="Time consent was granted")
    revoked_at: Optional[datetime] = Field(None, description="Time consent was revoked")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class ConsentListResponse(BaseModel):
    """Schema for list of consents."""
    
    total: int = Field(..., description="Total number of consent records")
    items: List[ConsentResponse] = Field(..., description="List of consents")


class ConsentAuditTrail(BaseModel):
    """Schema for consent audit trail."""
    
    consent_id: uuid.UUID = Field(..., description="Consent ID")
    patient_id: uuid.UUID = Field(..., description="Patient ID")
    purpose: str = Field(..., description="Purpose")
    action: str = Field(..., description="Action: GRANTED, REVOKED")
    timestamp: datetime = Field(..., description="Timestamp of action")
    ip_address: Optional[str] = Field(None, description="IP address")
    terms_version: str = Field(..., description="Terms version")


class ConsentHistoryResponse(BaseModel):
    """Schema for consent history."""
    
    patient_id: uuid.UUID = Field(..., description="Patient ID")
    total_consents: int = Field(..., description="Total consent records")
    active_consents: int = Field(..., description="Currently active consents")
    revoked_consents: int = Field(..., description="Revoked consents")
    audit_trail: List[ConsentAuditTrail] = Field(..., description="Audit trail")


class ConsentPurposes(BaseModel):
    """Schema for standard consent purposes."""
    
    purposes: List[str] = Field(
        default_factory=lambda: [
            "data_sharing",
            "abdm_integration",
            "fhir_export",
            "research",
            "quality_improvement",
            "third_party_analysis"
        ],
        description="List of available consent purposes"
    )


class ConsentRequest(BaseModel):
    """Schema for consent request."""
    
    patient_id: uuid.UUID = Field(..., description="Patient ID")
    session_id: uuid.UUID = Field(..., description="Session ID")
    purpose: str = Field(..., description="Purpose of consent")
    terms_version: str = Field("v1.0", description="Terms version")
