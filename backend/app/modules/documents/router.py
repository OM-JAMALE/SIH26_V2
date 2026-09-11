import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile, File, Query, status
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db
from app.core.utils import parse_uuid
from app.modules.documents.service import DocumentService
from app.modules.documents.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    EntityListResponse,
    ExtractedEntityResponse,
    DocumentDeleteResponse,
)

router = APIRouter()
document_service = DocumentService()


@router.post(
    "/{session_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Digitize Medical Document",
)
async def upload_document_endpoint(
    session_id: str,
    request: Request,
    file: UploadFile = File(...),
    db: DBSession = Depends(get_db),
):
    """Uploads a PDF, PNG, or JPEG medical document, runs deterministic OCR/extraction, and flags lab abnormalities."""
    request_id = getattr(request.state, "request_id", None)
    session_uuid = parse_uuid(session_id)
    doc = await document_service.upload_and_process_document(
        session_id=session_uuid,
        file=file,
        db=db,
        request_id=request_id,
    )
    return doc


@router.get(
    "/{session_id}/documents",
    response_model=DocumentListResponse,
    summary="List Uploaded Documents for Session",
)
def list_documents_endpoint(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    session_uuid = parse_uuid(session_id)
    docs = document_service.list_session_documents(session_id=session_uuid, db=db)
    return DocumentListResponse(documents=docs, total=len(docs))


@router.get(
    "/{session_id}/documents/{document_id}",
    response_model=DocumentUploadResponse,
    summary="Get Document Details and Extracted Entities",
)
def get_document_endpoint(
    session_id: str,
    document_id: str,
    db: DBSession = Depends(get_db),
):
    session_uuid = parse_uuid(session_id)
    doc_uuid = parse_uuid(document_id)
    doc = document_service.get_document(session_id=session_uuid, document_id=doc_uuid, db=db)
    return doc


@router.get(
    "/{session_id}/entities",
    response_model=EntityListResponse,
    summary="Get Extracted Clinical Entities for Session",
)
def list_session_entities_endpoint(
    session_id: str,
    abnormal_only: bool = Query(False, description="Filter only abnormal lab investigations"),
    db: DBSession = Depends(get_db),
):
    session_uuid = parse_uuid(session_id)
    entities = document_service.list_session_entities(
        session_id=session_uuid,
        db=db,
        abnormal_only=abnormal_only,
    )
    abnormal_count = sum(1 for e in entities if e.is_abnormal)
    return EntityListResponse(
        entities=[ExtractedEntityResponse.model_validate(e) for e in entities],
        total=len(entities),
        abnormal_count=abnormal_count,
    )


@router.delete(
    "/{session_id}/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete Document and Associated Extracted Entities",
)
def delete_document_endpoint(
    session_id: str,
    document_id: str,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    session_uuid = parse_uuid(session_id)
    doc_uuid = parse_uuid(document_id)
    return document_service.delete_document(
        session_id=session_uuid,
        document_id=doc_uuid,
        db=db,
        request_id=request_id,
    )
