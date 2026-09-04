import uuid
from app.db.models import (
    Patient,
    Session,
    ConversationTurn,
    Document,
    ExtractedEntity,
    Summary,
    Consent,
    AuditLog,
)


def test_patient_and_session_creation(db_session):
    patient = Patient(
        first_name="Rudra",
        last_name="Test",
        dob="1995-05-15",
        gender="male",
        contact_number="+919999999999",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    assert isinstance(patient.id, uuid.UUID)
    assert patient.first_name == "Rudra"

    session = Session(patient_id=patient.id, status="INITIATED")
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    assert session.patient_id == patient.id
    assert session.current_section == "CHIEF_COMPLAINT"


def test_conversation_and_summary_models(db_session):
    patient = Patient(first_name="Jane", last_name="Doe", dob="1990-01-01", gender="female")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, status="IN_CONVERSATION")
    db_session.add(session)
    db_session.commit()

    turn = ConversationTurn(
        session_id=session.id,
        turn_index=1,
        speaker="PATIENT",
        content="I have a headache.",
        section="CHIEF_COMPLAINT",
    )
    summary = Summary(
        session_id=session.id,
        chief_complaint="Headache",
        hpi="Patient reports acute headache.",
    )
    db_session.add_all([turn, summary])
    db_session.commit()

    assert turn.id is not None
    assert summary.session_id == session.id
    assert summary.status == "DRAFT"
