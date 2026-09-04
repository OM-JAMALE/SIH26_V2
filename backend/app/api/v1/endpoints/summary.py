import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db
from app.core.utils import parse_uuid
from app.modules.summary.service import ClinicalSummaryService
from app.api.v1.schemas.summary_api import (
    SummaryResponse,
    EditSummaryRequest,
    AcceptSummaryRequest,
    RejectSummaryRequest,
)

router = APIRouter()
summary_service = ClinicalSummaryService()


def _to_summary_response(summary_record) -> Dict[str, Any]:
    active = summary_record.physician_edited_summary or summary_record.structured_summary or {}
    return {
        "id": str(summary_record.id),
        "session_id": str(summary_record.session_id),
        "version": summary_record.version,
        "workflow_status": summary_record.workflow_status,
        "status": summary_record.status,
        "structured_summary": summary_record.structured_summary,
        "physician_edited_summary": summary_record.physician_edited_summary,
        "active_summary": active,
        "llm_model": summary_record.llm_model,
        "prompt_version": summary_record.prompt_version,
        "generation_error": summary_record.generation_error,
        "physician_notes": summary_record.physician_notes,
        "accepted_at": summary_record.accepted_at,
        "accepted_by": summary_record.accepted_by,
        "rejected_at": summary_record.rejected_at,
        "rejected_reason": summary_record.rejected_reason,
        "created_at": summary_record.created_at,
        "updated_at": summary_record.updated_at,
    }


@router.post(
    "/{session_id}/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate or Regenerate Clinical Summary for Session",
)
def generate_summary_endpoint(
    session_id: str,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    parsed_session_id = parse_uuid(session_id)
    summary_record = summary_service.generate_summary(parsed_session_id, db, request_id=request_id)
    return _to_summary_response(summary_record)


@router.get(
    "/{session_id}/summary",
    response_model=SummaryResponse,
    summary="Retrieve Clinical Summary for Session",
)
def get_summary_endpoint(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    parsed_session_id = parse_uuid(session_id)
    summary_record = summary_service.get_summary(parsed_session_id, db)
    return _to_summary_response(summary_record)


@router.patch(
    "/{session_id}/summary",
    response_model=SummaryResponse,
    summary="Physician Edit Structured Summary",
)
def edit_summary_endpoint(
    session_id: str,
    payload: EditSummaryRequest,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    parsed_session_id = parse_uuid(session_id)
    summary_record = summary_service.edit_summary(
        parsed_session_id, payload.edited_summary, db, request_id=request_id
    )
    return _to_summary_response(summary_record)


@router.post(
    "/{session_id}/summary/accept",
    response_model=SummaryResponse,
    summary="Physician Accept Clinical Summary",
)
def accept_summary_endpoint(
    session_id: str,
    payload: AcceptSummaryRequest,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    parsed_session_id = parse_uuid(session_id)
    summary_record = summary_service.accept_summary(
        parsed_session_id,
        physician_notes=payload.physician_notes,
        db=db,
        physician_id=payload.physician_id or "physician_1",
        request_id=request_id,
    )
    return _to_summary_response(summary_record)


@router.post(
    "/{session_id}/summary/reject",
    response_model=SummaryResponse,
    summary="Physician Reject Clinical Summary",
)
def reject_summary_endpoint(
    session_id: str,
    payload: RejectSummaryRequest,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    parsed_session_id = parse_uuid(session_id)
    summary_record = summary_service.reject_summary(
        parsed_session_id,
        reason=payload.reason,
        db=db,
        physician_id=payload.physician_id or "physician_1",
        request_id=request_id,
    )
    return _to_summary_response(summary_record)

