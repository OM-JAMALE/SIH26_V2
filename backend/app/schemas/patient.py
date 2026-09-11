"""Pydantic v2 schemas for Patient model."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import uuid


class PatientBase(BaseModel):
    """Base schema for Patient."""
    
    national_health_id: Optional[str] = Field(None, min_length=1, max_length=100, description="National Health ID")
    first_name: str = Field(..., min_length=1, max_length=100, description="Patient first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Patient last name")
    dob: str = Field(..., description="Date of birth in ISO format (YYYY-MM-DD)")
    gender: str = Field(..., min_length=1, max_length=20, description="Gender")
    contact_number: Optional[str] = Field(None, max_length=50, description="Contact number")

    @field_validator("dob")
    def validate_dob(cls, v):
        """Validate date of birth format."""
        try:
            datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError("DOB must be in ISO format YYYY-MM-DD")
        return v

    @field_validator("gender")
    def validate_gender(cls, v):
        """Validate gender value."""
        valid_genders = ["MALE", "FEMALE", "OTHER"]
        if v.upper() not in valid_genders:
            raise ValueError(f"Gender must be one of {valid_genders}")
        return v.upper()


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_number: Optional[str] = Field(None, max_length=50)


class PatientResponse(PatientBase):
    """Schema for patient response."""
    
    id: uuid.UUID = Field(..., description="Patient ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class PatientListResponse(BaseModel):
    """Schema for list of patients."""
    
    total: int = Field(..., description="Total number of patients")
    items: List[PatientResponse] = Field(..., description="List of patients")
