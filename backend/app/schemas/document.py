"""Pydantic v2 schemas for Document model."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class DocumentBase(BaseModel):
    """Base schema for Document."""
    
    filename: str = Field(..., min_length=1, max_length=255, description="File name")
    mime_type: str = Field(..., description="MIME type (application/pdf, image/png, image/jpeg)")
    file_size: int = Field(..., gt=0, description="File size in bytes")

    @field_validator("mime_type")
    def validate_mime_type(cls, v):
        """Validate MIME type."""
        valid_types = ["application/pdf", "image/png", "image/jpeg"]
        if v.lower() not in valid_types:
            raise ValueError(f"MIME type must be one of {valid_types}")
        return v.lower()

    @field_validator("file_size")
    def validate_file_size(cls, v):
        """Validate file size (max 25MB)."""
        max_size = 25 * 1024 * 1024  # 25MB
        if v > max_size:
            raise ValueError(f"File size must not exceed 25MB (got {v} bytes)")
        return v


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")


class DocumentUpdate(BaseModel):
    """Schema for updating document."""
    
    processing_status: Optional[str] = Field(None, description="Processing status")
    raw_text: Optional[str] = Field(None, description="Extracted raw text")


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    
    id: uuid.UUID = Field(..., description="Document ID")
    session_id: uuid.UUID = Field(..., description="Session ID")
    processing_status: str = Field(..., description="Processing status")
    raw_text: Optional[str] = Field(None, description="Extracted raw text")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents."""
    
    total: int = Field(..., description="Total number of documents")
    items: List[DocumentResponse] = Field(..., description="List of documents")


class DocumentUploadRequest(BaseModel):
    """Schema for document upload request."""
    
    session_id: uuid.UUID = Field(..., description="Session ID")
    # File data is handled separately via multipart form


class DocumentUploadResponse(DocumentResponse):
    """Schema for document upload response."""
    
    extraction_status: str = Field(..., description="Extraction status")
    entities_extracted: int = Field(0, description="Number of entities extracted")
