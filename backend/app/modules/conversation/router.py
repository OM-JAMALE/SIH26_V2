import uuid
from typing import List, Dict, Any, Union
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db
from app.core.utils import parse_uuid
from app.modules.conversation.service import ClinicalConversationService
from app.modules.conversation.schemas import (
    CreateSessionRequest,
    AcknowledgeDisclaimerRequest,
    SubmitResponseRequest,
    SessionStateResponse,
    ProcessResponseResult,
    TurnResponse,
)

router = APIRouter()
conversation_service = ClinicalConversationService()


@router.post(
    "",
    response_model=SessionStateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Clinical Interview Session",
)
def create_session_endpoint(
    payload: CreateSessionRequest,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    patient_uuid = parse_uuid(payload.patient_id)
    session = conversation_service.create_session(
        patient_id=patient_uuid,
        mode=payload.mode,
        disclaimer_acknowledged=payload.disclaimer_acknowledged,
        db=db,
        request_id=request_id,
    )
    return conversation_service.get_session_state(session.id, db)


@router.post(
    "/{session_id}/disclaimer",
    response_model=SessionStateResponse,
    summary="Acknowledge Initial Safety Disclaimer",
)
def acknowledge_disclaimer_endpoint(
    session_id: str,
    payload: AcknowledgeDisclaimerRequest,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    parsed_session_id = parse_uuid(session_id)
    conversation_service.acknowledge_disclaimer(parsed_session_id, db, request_id=request_id)
    return conversation_service.get_session_state(parsed_session_id, db)


@router.get(
    "/{session_id}",
    response_model=SessionStateResponse,
    summary="Get Current Clinical Interview Session State",
)
def get_session_state_endpoint(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    parsed_session_id = parse_uuid(session_id)
    return conversation_service.get_session_state(parsed_session_id, db)


@router.post(
    "/{session_id}/responses",
    response_model=ProcessResponseResult,
    summary="Submit Patient Response & Progress Interview State",
)
def submit_response_endpoint(
    session_id: str,
    payload: SubmitResponseRequest,
    request: Request,
    db: DBSession = Depends(get_db),
):
    request_id = getattr(request.state, "request_id", None)
    parsed_session_id = parse_uuid(session_id)
    return conversation_service.submit_patient_response(
        session_id=parsed_session_id,
        raw_text=payload.text,
        db=db,
        request_id=request_id,
    )


@router.get(
    "/{session_id}/conversation",
    response_model=List[TurnResponse],
    summary="Get Full Conversation Turn History",
)
def get_conversation_history_endpoint(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    parsed_session_id = parse_uuid(session_id)
    turns = conversation_service.get_conversation_history(parsed_session_id, db)
    return [
        {
            "id": str(t.id),
            "session_id": str(t.session_id),
            "turn_index": t.turn_index,
            "speaker": t.speaker,
            "content": t.content,
            "extracted_data": t.extracted_data or {},
            "safety_alerts": t.safety_alerts or {},
            "section": t.section,
            "created_at": t.created_at,
        }
        for t in turns
    ]
