"""Unit tests for ClinicalConversationService (Module A)."""

import pytest
import uuid
from app.modules.conversation.service import ClinicalConversationService
from app.modules.conversation.schemas import SessionMode, InterviewState, SessionLifecycle
from app.db.models.patient import Patient


@pytest.fixture
def test_patient(db_session):
    """Fixture creating a test patient."""
    patient = Patient(
        id=uuid.uuid4(),
        first_name="Test",
        last_name="Patient",
        gender="Male",
        dob="1990-01-01",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


def test_start_conversation(db_session, test_patient):
    """Verify session starts in IDENTIFICATION state."""
    service = ClinicalConversationService()
    session = service.create_session(
        patient_id=test_patient.id,
        mode=SessionMode.MODERN,
        disclaimer_acknowledged=True,
        db=db_session
    )
    
    assert session.id is not None
    assert session.patient_id == test_patient.id
    assert session.current_section == InterviewState.IDENTIFICATION.value
    assert session.mode == "MODERN"
    assert session.disclaimer_acknowledged is True


def test_advance_section(db_session, test_patient):
    """Verify processing turn advances conversation."""
    service = ClinicalConversationService()
    session = service.create_session(
        patient_id=test_patient.id,
        mode=SessionMode.MODERN,
        disclaimer_acknowledged=True,
        db=db_session
    )
    
    result = service.submit_patient_response(
        session_id=session.id,
        raw_text="I have severe headache for 3 days.",
        db=db_session
    )
    assert result.session_id == str(session.id)
    assert result.next_question is not None


def test_cannot_skip_sections(db_session, test_patient):
    """Verify state machine enforces section ordering."""
    service = ClinicalConversationService()
    session = service.create_session(
        patient_id=test_patient.id,
        mode=SessionMode.MODERN,
        disclaimer_acknowledged=True,
        db=db_session
    )
    assert session.current_section == InterviewState.IDENTIFICATION.value
    assert session.lifecycle_status != SessionLifecycle.COMPLETED.value


def test_save_turn(db_session, test_patient):
    """Verify conversation turns are saved."""
    service = ClinicalConversationService()
    session = service.create_session(
        patient_id=test_patient.id,
        mode=SessionMode.MODERN,
        disclaimer_acknowledged=True,
        db=db_session
    )
    service.submit_patient_response(
        session_id=session.id,
        raw_text="I feel feverish and fatigued.",
        db=db_session
    )
    turns = service.get_conversation_history(session.id, db=db_session)
    assert len(turns) >= 2


def test_resume_after_restart(db_session, test_patient):
    """Verify conversation state can be loaded after server restart."""
    service1 = ClinicalConversationService()
    session = service1.create_session(
        patient_id=test_patient.id,
        mode=SessionMode.MODERN,
        disclaimer_acknowledged=True,
        db=db_session
    )
    
    service2 = ClinicalConversationService()
    state = service2.get_session_state(session.id, db=db_session)
    assert state.session_id == str(session.id)
    assert state.patient_id == str(test_patient.id)
