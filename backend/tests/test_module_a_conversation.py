import uuid
import pytest
from fastapi.testclient import TestClient

from app.db.models.patient import Patient
from app.db.models.session import Session
from app.modules.conversation.schemas import (
    InterviewState,
    SocratesAttribute,
    SessionLifecycle,
    SessionMode,
    ClinicalHistory,
    StructuredExtraction,
    InformationStatus,
    ChiefComplaintItem,
)
from app.modules.conversation.state_machine import InterviewStateMachine, update_clinical_history
from app.modules.conversation.safety import SafetyRulesEngine
from app.modules.conversation.extraction import MockExtractionProvider
from app.modules.conversation.service import ClinicalConversationService
from app.modules.conversation.questions import (
    INITIAL_DISCLAIMER_TEXT,
    DETERMINISTIC_EMERGENCY_MESSAGE,
    NO_DIAGNOSIS_TREATMENT_ADVICE_RESPONSE,
)


# =====================================================================
# 1. STATE MACHINE & SOCRATES TESTS
# =====================================================================

def test_state_machine_socrates_progression():
    sm = InterviewStateMachine()
    history = ClinicalHistory()
    extraction = StructuredExtraction(
        extracted_symptoms=[ChiefComplaintItem(symptom="Chest pain", status=InformationStatus.PRESENT)]
    )

    # IDENTIFICATION -> CHIEF_COMPLAINT
    state, soc, lc = sm.advance_state(InterviewState.IDENTIFICATION, None, history, extraction)
    assert state == InterviewState.CHIEF_COMPLAINT
    assert lc == SessionLifecycle.IN_PROGRESS

    # CHIEF_COMPLAINT -> HPI (SITE)
    state, soc, lc = sm.advance_state(InterviewState.CHIEF_COMPLAINT, None, history, extraction)
    assert state == InterviewState.HPI
    assert soc == SocratesAttribute.SITE

    # HPI (SITE) -> HPI (ONSET)
    state, soc, lc = sm.advance_state(InterviewState.HPI, SocratesAttribute.SITE, history, extraction)
    assert state == InterviewState.HPI
    assert soc == SocratesAttribute.ONSET

    # HPI (SEVERITY) -> PAST_MEDICAL_HISTORY
    state, soc, lc = sm.advance_state(InterviewState.HPI, SocratesAttribute.SEVERITY, history, extraction)
    assert state == InterviewState.PAST_MEDICAL_HISTORY
    assert soc is None


# =====================================================================
# 2. EXTRACTION SCHEMA TESTS (KNOWN VS DENIED VS UNKNOWN)
# =====================================================================

def test_extraction_distinguishes_denied_from_unknown():
    mock_extractor = MockExtractionProvider()
    
    # Explicit denial
    res_denied = mock_extractor.extract("I do not have fever or cough", "CHIEF_COMPLAINT", "SITE")
    assert "fever" in res_denied.denied_symptoms or "cough" in res_denied.denied_symptoms

    # Present symptom
    res_present = mock_extractor.extract("I have a severe headache", "CHIEF_COMPLAINT", "SITE")
    assert len(res_present.extracted_symptoms) > 0
    assert res_present.extracted_symptoms[0].status == InformationStatus.PRESENT

    # Unknown / Not asked -> remains empty/unknown in history object
    history = ClinicalHistory()
    assert len(history.allergies) == 0  # Unknown, not converted to denied


# =====================================================================
# 3. DETERMINISTIC RED-FLAG SAFETY RULE TESTS
# =====================================================================

def test_safety_rules_engine_chest_pain():
    engine = SafetyRulesEngine()
    extraction = StructuredExtraction(
        extracted_symptoms=[ChiefComplaintItem(symptom="Severe chest pain", status=InformationStatus.PRESENT)]
    )
    alert = engine.evaluate_safety("I am having acute chest pain right now", extraction)

    assert alert.flagged is True
    assert alert.rule_id == "RULE_CHEST_PAIN_ACUTE"
    assert alert.emergency_message == DETERMINISTIC_EMERGENCY_MESSAGE


def test_safety_rules_engine_denied_chest_pain():
    engine = SafetyRulesEngine()
    # Explicitly denied chest pain should NOT trigger red flag
    extraction = StructuredExtraction(
        extracted_symptoms=[ChiefComplaintItem(symptom="Chest pain", status=InformationStatus.DENIED)]
    )
    alert = engine.evaluate_safety("No chest pain at all", extraction)
    assert alert.flagged is False


def test_safety_rules_engine_all_red_flags():
    engine = SafetyRulesEngine()
    
    # Test Dyspnea
    assert engine.evaluate_safety("I cannot breathe at all", StructuredExtraction()).flagged is True
    # Test Loss of Consciousness
    assert engine.evaluate_safety("I passed out on the floor", StructuredExtraction()).flagged is True
    # Test Neurological Deficit
    assert engine.evaluate_safety("Sudden facial droop and slurred speech", StructuredExtraction()).flagged is True
    # Test Uncontrolled Bleeding
    assert engine.evaluate_safety("I am coughing blood", StructuredExtraction()).flagged is True
    # Test Anaphylaxis
    assert engine.evaluate_safety("My throat is closing up", StructuredExtraction()).flagged is True
    # Test Suicidal Ideation
    assert engine.evaluate_safety("I want to kill myself", StructuredExtraction()).flagged is True


# =====================================================================
# 4. SERVICE & API FLOW TESTS
# =====================================================================

def test_session_creation_and_disclaimer_acknowledgement(client: TestClient, db_session):
    patient = Patient(first_name="Jane", last_name="Doe", dob="1990-01-01", gender="female")
    db_session.add(patient)
    db_session.commit()

    # 1. Create Session without disclaimer
    create_res = client.post(
        "/api/v1/sessions",
        json={"patient_id": str(patient.id), "mode": "MODERN", "disclaimer_acknowledged": False},
    )
    assert create_res.status_code == 201
    s_data = create_res.json()
    session_id = s_data["session_id"]
    assert s_data["disclaimer_acknowledged"] is False
    assert s_data["lifecycle_status"] == "CREATED"

    # 2. Attempt response before disclaimer -> 403 Forbidden
    resp_fail = client.post(f"/api/v1/sessions/{session_id}/responses", json={"text": "I have headache"})
    assert resp_fail.status_code == 403
    assert resp_fail.json()["detail"]["code"] == "DISCLAIMER_NOT_ACKNOWLEDGED"

    # 3. Acknowledge disclaimer
    ack_res = client.post(f"/api/v1/sessions/{session_id}/disclaimer", json={"disclaimer_acknowledged": True})
    assert ack_res.status_code == 200
    assert ack_res.json()["disclaimer_acknowledged"] is True
    assert ack_res.json()["lifecycle_status"] == "IN_PROGRESS"

    # 4. Submit response for IDENTIFICATION turn -> moves to CHIEF_COMPLAINT
    sub_res = client.post(f"/api/v1/sessions/{session_id}/responses", json={"text": "My name is Jane Doe, age 34"})
    assert sub_res.status_code == 200
    res_json = sub_res.json()
    assert res_json["current_section"] == "CHIEF_COMPLAINT"

    # 5. Submit response for CHIEF_COMPLAINT turn -> moves to HPI
    sub_res2 = client.post(f"/api/v1/sessions/{session_id}/responses", json={"text": "I have headache since yesterday"})
    assert sub_res2.status_code == 200
    res_json2 = sub_res2.json()
    assert res_json2["current_section"] == "HPI"
    assert res_json2["socrates_state"] == "SITE"



def test_safety_escalation_flow(client: TestClient, db_session):
    patient = Patient(first_name="Robert", last_name="Smith", dob="1975-06-15", gender="male")
    db_session.add(patient)
    db_session.commit()

    create_res = client.post(
        "/api/v1/sessions",
        json={"patient_id": str(patient.id), "mode": "MODERN", "disclaimer_acknowledged": True},
    )
    session_id = create_res.json()["session_id"]

    # Submit emergency symptom: chest pain
    sub_res = client.post(f"/api/v1/sessions/{session_id}/responses", json={"text": "I have severe crushing chest pain"})
    assert sub_res.status_code == 200
    res_json = sub_res.json()

    assert res_json["lifecycle_status"] == "SAFETY_ESCALATED"
    assert res_json["safety"]["flagged"] is True
    assert res_json["safety"]["rule_id"] == "RULE_CHEST_PAIN_ACUTE"
    assert DETERMINISTIC_EMERGENCY_MESSAGE in res_json["next_question"]

    # Further responses to escalated session must be blocked
    block_res = client.post(f"/api/v1/sessions/{session_id}/responses", json={"text": "Hello?"})
    assert block_res.status_code == 400
    assert block_res.json()["detail"]["code"] == "SESSION_NOT_IN_PROGRESS"


def test_diagnosis_treatment_advice_boundary(client: TestClient, db_session):
    patient = Patient(first_name="Mark", last_name="Taylor", dob="1988-02-10", gender="male")
    db_session.add(patient)
    db_session.commit()

    create_res = client.post(
        "/api/v1/sessions",
        json={"patient_id": str(patient.id), "mode": "MODERN", "disclaimer_acknowledged": True},
    )
    session_id = create_res.json()["session_id"]

    # Submit response asking for diagnosis
    sub_res = client.post(f"/api/v1/sessions/{session_id}/responses", json={"text": "What medicine should I take for my headache? What do I have?"})
    assert sub_res.status_code == 200
    res_json = sub_res.json()
    assert NO_DIAGNOSIS_TREATMENT_ADVICE_RESPONSE in res_json["next_question"]


def test_ayush_mode_questions(client: TestClient, db_session):
    patient = Patient(first_name="Priya", last_name="Sharma", dob="1994-09-09", gender="female")
    db_session.add(patient)
    db_session.commit()

    create_res = client.post(
        "/api/v1/sessions",
        json={"patient_id": str(patient.id), "mode": "AYUSH", "disclaimer_acknowledged": True},
    )
    session_id = create_res.json()["session_id"]

    state_res = client.get(f"/api/v1/sessions/{session_id}")
    assert state_res.status_code == 200
    assert state_res.json()["mode"] == "AYUSH"
    assert "Namaste" in state_res.json()["latest_question"]
