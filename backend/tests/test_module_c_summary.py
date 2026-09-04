import uuid
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient

from app.db.models.patient import Patient
from app.db.models.session import Session
from app.db.models.conversation_turn import ConversationTurn
from app.db.models.summary import Summary
from app.ai.schemas.summary import (
    ClinicalSummarySchema,
    ClinicalItem,
    MedicationItem,
    LabInvestigation,
    RedFlagItem,
    InformationStatus,
)
from app.ai.providers import MockLLMProvider
from app.modules.summary.service import ClinicalSummaryService


# =====================================================================
# 1. SCHEMA TESTS
# =====================================================================

def test_clinical_summary_schema_valid():
    summary = ClinicalSummarySchema(
        session_id=str(uuid.uuid4()),
        chief_complaint=[
            ClinicalItem(name="Chest pain", status=InformationStatus.KNOWN, details="Acute retrosternal pressure")
        ],
        relevant_negative_findings=[
            ClinicalItem(name="Shortness of breath", status=InformationStatus.DENIED, details="Explicitly denied dyspnea")
        ],
        information_gaps=["Lipid panel not provided"],
        generated_summary_text="Patient presents with acute chest pain.",
    )
    assert summary.session_id is not None
    assert summary.chief_complaint[0].status == InformationStatus.KNOWN
    assert summary.relevant_negative_findings[0].status == InformationStatus.DENIED
    # Verify distinction: missing info != negative finding
    assert summary.relevant_negative_findings[0].status != InformationStatus.NOT_PROVIDED


def test_clinical_summary_schema_invalid_type():
    with pytest.raises(ValidationError):
        ClinicalSummarySchema(
            session_id=12345,  # Should be string
            chief_complaint="Invalid string instead of list",
            generated_summary_text=None,
        )


# =====================================================================
# 2. PROVIDER TESTS
# =====================================================================

def test_mock_llm_provider_success():
    provider = MockLLMProvider()
    result = provider.generate_structured(
        prompt="SESSION ID: test-123\nchief complaint: chest pain",
        system_prompt="system prompt",
        schema_class=ClinicalSummarySchema,
    )
    assert isinstance(result, ClinicalSummarySchema)
    assert result.session_id == "test-123"
    assert len(result.chief_complaint) > 0
    assert len(result.red_flags) > 0



def test_mock_llm_provider_simulation_failure():
    provider = MockLLMProvider()
    with pytest.raises(ValueError):
        provider.generate_structured(
            prompt="SIMULATE_INVALID_JSON_RESPONSE",
            system_prompt="system prompt",
            schema_class=ClinicalSummarySchema,
        )


# =====================================================================
# 3. SERVICE & WORKFLOW TESTS
# =====================================================================

def test_summary_service_generate_and_workflow(db_session):
    patient = Patient(first_name="Alice", last_name="Smith", dob="1985-04-12", gender="female")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, status="IN_CONVERSATION")
    db_session.add(session)
    db_session.commit()

    turn = ConversationTurn(
        session_id=session.id,
        turn_index=1,
        speaker="PATIENT",
        content="I have retrosternal chest pain onset 2 hours ago.",
        section="CHIEF_COMPLAINT",
    )
    db_session.add(turn)
    db_session.commit()

    service = ClinicalSummaryService(provider_type="mock")
    summary_record = service.generate_summary(session.id, db_session)

    assert summary_record.session_id == session.id
    assert summary_record.workflow_status == "PHYSICIAN_REVIEW"
    assert summary_record.structured_summary is not None
    assert summary_record.structured_summary["session_id"] == str(session.id)

    # Edit summary
    edits = {
        "generated_summary_text": "Physician edited narrative summary text.",
        "chief_complaint": [{"name": "Edited Chest Pain", "status": "KNOWN"}],
    }
    edited_record = service.edit_summary(session.id, edits, db_session)
    assert edited_record.physician_edited_summary is not None
    assert edited_record.physician_edited_summary["generated_summary_text"] == "Physician edited narrative summary text."
    # Original AI structured summary remains preserved
    assert edited_record.structured_summary["generated_summary_text"] != "Physician edited narrative summary text."

    # Accept summary
    accepted_record = service.accept_summary(session.id, "Approved by Dr. House", db_session, physician_id="doc_1")
    assert accepted_record.workflow_status == "ACCEPTED"
    assert accepted_record.accepted_by == "doc_1"
    assert accepted_record.accepted_at is not None


def test_invalid_workflow_transition(db_session):
    patient = Patient(first_name="Bob", last_name="Jones", dob="1970-01-01", gender="male")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, status="IN_CONVERSATION")
    db_session.add(session)
    db_session.commit()

    service = ClinicalSummaryService(provider_type="mock")
    summary_record = service.generate_summary(session.id, db_session)
    service.accept_summary(session.id, "Approved", db_session)

    # Attempt invalid transition from ACCEPTED to REJECTED or GENERATING directly
    with pytest.raises(Exception):
        service.reject_summary(session.id, "Cannot reject accepted summary", db_session)


# =====================================================================
# 4. API INTEGRATION TESTS
# =====================================================================

def test_summary_api_full_flow(client: TestClient, db_session):
    # 1. Create Patient & Session
    patient = Patient(first_name="Charlie", last_name="Brown", dob="1980-08-20", gender="male")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, status="INITIATED")
    db_session.add(session)
    db_session.commit()

    session_id_str = str(session.id)

    # 2. POST Generate Summary
    gen_res = client.post(f"/api/v1/sessions/{session_id_str}/summary")
    assert gen_res.status_code == 201
    gen_data = gen_res.json()
    assert gen_data["session_id"] == session_id_str
    assert gen_data["workflow_status"] == "PHYSICIAN_REVIEW"
    assert "structured_summary" in gen_data

    # 3. GET Summary
    get_res = client.get(f"/api/v1/sessions/{session_id_str}/summary")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == gen_data["id"]

    # 4. PATCH Edit Summary
    edit_payload = {
        "edited_summary": {
            "session_id": session_id_str,
            "generated_summary_text": "Updated summary text by physician.",
            "chief_complaint": [{"name": "Severe chest pressure", "status": "KNOWN"}],
        }
    }
    patch_res = client.patch(f"/api/v1/sessions/{session_id_str}/summary", json=edit_payload)
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["physician_edited_summary"]["generated_summary_text"] == "Updated summary text by physician."

    # 5. POST Accept Summary
    accept_payload = {"physician_notes": "Reviewed and verified.", "physician_id": "dr_smith"}
    accept_res = client.post(f"/api/v1/sessions/{session_id_str}/summary/accept", json=accept_payload)
    assert accept_res.status_code == 200
    accept_data = accept_res.json()
    assert accept_data["workflow_status"] == "ACCEPTED"
    assert accept_data["accepted_by"] == "dr_smith"


def test_summary_api_reject_flow(client: TestClient, db_session):
    patient = Patient(first_name="David", last_name="Miller", dob="1992-11-11", gender="male")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, status="INITIATED")
    db_session.add(session)
    db_session.commit()

    session_id_str = str(session.id)

    # Generate
    client.post(f"/api/v1/sessions/{session_id_str}/summary")

    # Reject
    reject_payload = {"reason": "Missing recent ECG document findings", "physician_id": "dr_adams"}
    reject_res = client.post(f"/api/v1/sessions/{session_id_str}/summary/reject", json=reject_payload)
    assert reject_res.status_code == 200
    assert reject_res.json()["workflow_status"] == "REJECTED"
    assert reject_res.json()["rejected_reason"] == "Missing recent ECG document findings"


def test_summary_api_nonexistent_session(client: TestClient):
    fake_uuid = str(uuid.uuid4())
    res = client.get(f"/api/v1/sessions/{fake_uuid}/summary")
    assert res.status_code == 404
    assert res.json()["detail"]["code"] == "SUMMARY_NOT_FOUND"

