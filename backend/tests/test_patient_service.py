import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.models.patient import Patient as PatientModel
from app.db.models.session import Session as SessionModel
from app.modules.patient.service import PatientService
from app.modules.patient.schemas import PatientCreateRequest

client = TestClient(app)
patient_service = PatientService()


def test_create_and_get_patient(db_session):
    """Test patient creation and retrieval via PatientService."""
    req = PatientCreateRequest(
        first_name="Anita",
        last_name="Sharma",
        dob="1992-04-12",
        gender="Female",
        national_health_id="91-9999-8888-7777",
        contact_number="+91-9812345678",
    )
    patient = patient_service.create_or_get_patient(db=db_session, payload=req)
    assert patient.id is not None
    assert patient.first_name == "Anita"
    assert patient.national_health_id == "91-9999-8888-7777"

    # Retrieve again with same ABHA ID (should return existing)
    existing = patient_service.create_or_get_patient(db=db_session, payload=req)
    assert existing.id == patient.id

    # Fetch by ID
    fetched = patient_service.get_patient(db=db_session, patient_id=patient.id)
    assert fetched.first_name == "Anita"


def test_patient_session_history(db_session):
    """Test retrieving session history for returning patient."""
    patient = PatientModel(
        first_name="Rohan",
        last_name="Verma",
        dob="1988-11-20",
        gender="Male",
        national_health_id="91-1111-2222-3333",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    s1 = SessionModel(
        patient_id=patient.id,
        mode="MODERN",
        status="COMPLETED",
        lifecycle_status="COMPLETED",
        structured_history={"chief_complaint": {"symptom": "Fever and chills"}},
    )
    s2 = SessionModel(
        patient_id=patient.id,
        mode="MODERN",
        status="IN_CONVERSATION",
        lifecycle_status="IN_PROGRESS",
        structured_history={"chief_complaint": {"symptom": "Severe migraine"}},
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    sessions = patient_service.get_patient_sessions(db=db_session, patient_id=patient.id)
    assert len(sessions) == 2
    # Should be sorted descending by created_at
    assert sessions[0].chief_complaint in ["Fever and chills", "Severe migraine"]


def test_doctor_search_patients(db_session):
    """Test searching patients by ABHA, name, or contact number for doctor portal."""
    patient = PatientModel(
        first_name="Suresh",
        last_name="Patel",
        dob="1975-01-05",
        gender="Male",
        national_health_id="91-5555-4444-3333",
        contact_number="9876543210",
    )
    db_session.add(patient)
    db_session.commit()

    # Search by ABHA
    res_abha = patient_service.search_patients_for_doctor(db=db_session, query="91-5555")
    assert len(res_abha) == 1
    assert res_abha[0].first_name == "Suresh"

    # Search by name
    res_name = patient_service.search_patients_for_doctor(db=db_session, query="Patel")
    assert len(res_name) == 1
    assert res_name[0].last_name == "Patel"

    # Search by UUID
    res_uuid = patient_service.search_patients_for_doctor(db=db_session, query=str(patient.id))
    assert len(res_uuid) == 1
    assert res_uuid[0].id == str(patient.id)


def test_patient_and_doctor_api_endpoints(db_session):
    """Test HTTP API endpoints for Patient and Doctor routes."""
    # 1. Create Patient
    create_resp = client.post(
        "/api/v1/patients",
        json={
            "first_name": "Priya",
            "last_name": "Singh",
            "dob": "1995-08-30",
            "gender": "Female",
            "national_health_id": "91-7777-6666-5555",
            "contact_number": "+91-9988776655",
        },
    )
    assert create_resp.status_code == 201
    p_data = create_resp.json()
    p_id = p_data["id"]

    # 2. Get Patient by ID
    get_resp = client.get(f"/api/v1/patients/{p_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["first_name"] == "Priya"

    # 3. Get Sessions (initially empty)
    sessions_resp = client.get(f"/api/v1/patients/{p_id}/sessions")
    assert sessions_resp.status_code == 200
    assert isinstance(sessions_resp.json(), list)

    # 4. Doctor Search
    search_resp = client.get("/api/v1/doctors/patients/search?query=Priya")
    assert search_resp.status_code == 200
    search_results = search_resp.json()
    assert len(search_results) >= 1
    assert search_results[0]["first_name"] == "Priya"

    # 5. Doctor Full History
    history_resp = client.get(f"/api/v1/doctors/patients/{p_id}/full-history")
    assert history_resp.status_code == 200
    h_data = history_resp.json()
    assert h_data["patient"]["first_name"] == "Priya"
    assert "sessions" in h_data
