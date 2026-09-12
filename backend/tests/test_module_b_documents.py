import io
import uuid
import pytest
from fastapi.testclient import TestClient

from app.db.models.patient import Patient
from app.db.models.session import Session
from app.db.models.document import Document
from app.db.models.extracted_entity import ExtractedEntity
from app.db.models.audit_log import AuditLog
from app.modules.documents.lab_rules import (
    parse_reference_range,
    parse_numeric_value,
    evaluate_lab_result,
)
from app.modules.documents.schemas import (
    EntityItemSchema,
    DocumentExtractionSchema,
)


# =====================================================================
# 1. DETERMINISTIC LAB RULES TESTS
# =====================================================================

def test_parse_reference_range():
    assert parse_reference_range("13.0 - 17.5 g/dL") == (13.0, 17.5)
    assert parse_reference_range("70 to 99") == (70.0, 99.0)
    assert parse_reference_range("< 200 mg/dL") == (None, 200.0)
    assert parse_reference_range("<= 150") == (None, 150.0)
    assert parse_reference_range("> 40") == (40.0, None)
    assert parse_reference_range(">= 40.5") == (40.5, None)
    assert parse_reference_range(None) == (None, None)
    assert parse_reference_range("not a range") == (None, None)


def test_parse_numeric_value():
    assert parse_numeric_value("142.5 mg/dL") == 142.5
    assert parse_numeric_value("0.04") == 0.04
    assert parse_numeric_value("-5.2") == -5.2
    assert parse_numeric_value(None) is None
    assert parse_numeric_value("invalid") is None


def test_deterministic_lab_abnormality_evaluation():
    # 1. High Glucose with custom range
    is_abnormal, flag, ref_range = evaluate_lab_result(
        test_name="Fasting Glucose",
        raw_value="145 mg/dL",
        numeric_value=145.0,
        unit="mg/dL",
        reference_range="70.0 - 99.0 mg/dL",
    )
    assert is_abnormal is True
    assert flag == "HIGH"
    assert "70.0 - 99.0" in ref_range

    # 2. Normal Glucose with custom range
    is_abnormal, flag, _ = evaluate_lab_result(
        test_name="Fasting Glucose",
        raw_value="88 mg/dL",
        numeric_value=88.0,
        reference_range="70.0 - 99.0",
    )
    assert is_abnormal is False
    assert flag == "NORMAL"

    # 3. Low Glucose (Hypoglycemia)
    is_abnormal, flag, _ = evaluate_lab_result(
        test_name="Fasting Glucose",
        raw_value="55 mg/dL",
        numeric_value=55.0,
        reference_range="70.0 - 99.0",
    )
    assert is_abnormal is True
    assert flag == "LOW"

    # 4. Standard Database lookup when reference_range is None
    is_abnormal, flag, resolved = evaluate_lab_result(
        test_name="Hemoglobin",
        raw_value="10.2 g/dL",
        numeric_value=10.2,
    )
    assert is_abnormal is True
    assert flag == "LOW"
    assert "13.0 - 17.5" in resolved

    # 5. Normal Creatinine standard lookup
    is_abnormal, flag, _ = evaluate_lab_result(
        test_name="Serum Creatinine",
        raw_value="0.9 mg/dL",
        numeric_value=0.9,
    )
    assert is_abnormal is False
    assert flag == "NORMAL"

    # 6. Upper-bound only (< 200 for cholesterol)
    is_abnormal, flag, _ = evaluate_lab_result(
        test_name="Total Cholesterol",
        raw_value="240 mg/dL",
        numeric_value=240.0,
        reference_range="< 200 mg/dL",
    )
    assert is_abnormal is True
    assert flag == "HIGH"

    # 7. Lower-bound only (> 40 for HDL)
    is_abnormal, flag, _ = evaluate_lab_result(
        test_name="HDL Cholesterol",
        raw_value="32 mg/dL",
        numeric_value=32.0,
        reference_range="> 40 mg/dL",
    )
    assert is_abnormal is True
    assert flag == "LOW"

    # 8. Comma thousands separator parsing
    assert parse_reference_range("150,000 - 450,000") == (150000.0, 450000.0)
    assert parse_numeric_value("250,000") == 250000.0

    # 9. Priority matching: HDL Cholesterol must match HDL (> 40), not general cholesterol (< 200)
    is_abnormal, flag, resolved = evaluate_lab_result(
        test_name="HDL Cholesterol",
        raw_value="35 mg/dL",
        numeric_value=35.0,
    )
    assert is_abnormal is True
    assert flag == "LOW"
    assert "> 40.0" in resolved


# =====================================================================
# 2. API ENDPOINT & SERVICE PIPELINE TESTS
# =====================================================================

def test_document_upload_mime_validation(client: TestClient, db_session):
    # Setup patient and session
    patient = Patient(first_name="John", last_name="Doe", dob="1980-01-01", gender="male")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, mode="MODERN", lifecycle_status="IN_PROGRESS")
    db_session.add(session)
    db_session.commit()

    # Case 1: Unauthorized file type (.exe / application/x-executable)
    fake_exe = io.BytesIO(b"MZ\x90\x00executable content")
    response = client.post(
        f"/api/v1/sessions/{session.id}/documents",
        files={"file": ("malicious.exe", fake_exe, "application/x-executable")},
    )
    assert response.status_code == 415
    data = response.json()
    assert data["detail"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

    # Case 2: Spoofed extension (.exe with application/pdf MIME)
    fake_payload = io.BytesIO(b"binary payload")
    response_spoofed_ext = client.post(
        f"/api/v1/sessions/{session.id}/documents",
        files={"file": ("exploit.exe", fake_payload, "application/pdf")},
    )
    assert response_spoofed_ext.status_code == 415
    assert response_spoofed_ext.json()["detail"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

    # Case 3: Spoofed MIME (application/x-msdownload with .pdf extension)
    response_spoofed_mime = client.post(
        f"/api/v1/sessions/{session.id}/documents",
        files={"file": ("doc.pdf", fake_payload, "application/x-msdownload")},
    )
    assert response_spoofed_mime.status_code == 415
    assert response_spoofed_mime.json()["detail"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_document_upload_size_limit(client: TestClient, db_session):
    patient = Patient(first_name="Jane", last_name="Doe", dob="1992-05-10", gender="female")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, mode="MODERN", lifecycle_status="IN_PROGRESS")
    db_session.add(session)
    db_session.commit()

    # Create oversized payload (> 25MB: 26 * 1024 * 1024 bytes)
    oversized = io.BytesIO(b"a" * (26 * 1024 * 1024))
    response = client.post(
        f"/api/v1/sessions/{session.id}/documents",
        files={"file": ("large_report.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "FILE_TOO_LARGE"


def test_document_upload_session_not_found(client: TestClient):
    random_id = uuid.uuid4()
    pdf_bytes = io.BytesIO(b"%PDF-1.4 mock pdf text content")
    response = client.post(
        f"/api/v1/sessions/{random_id}/documents",
        files={"file": ("report.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "SESSION_NOT_FOUND"


def test_document_upload_and_extraction_pipeline_success(client: TestClient, db_session):
    # 1. Seed session
    patient = Patient(first_name="Alice", last_name="Wonder", dob="1988-03-22", gender="female")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, mode="MODERN", lifecycle_status="IN_PROGRESS")
    db_session.add(session)
    db_session.commit()

    # 2. Upload lab report with glucose and troponin findings
    report_content = b"%PDF-1.4 lab test report: Fasting blood sugar and Troponin I test results."
    pdf_file = io.BytesIO(report_content)

    response = client.post(
        f"/api/v1/sessions/{session.id}/documents",
        files={"file": ("blood_test.pdf", pdf_file, "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()

    assert data["filename"] == "blood_test.pdf"
    assert data["mime_type"] == "application/pdf"
    assert data["processing_status"] == "EXTRACTED"
    assert "id" in data
    doc_id = data["id"]

    # 3. Verify Database entities created
    db_session.expire_all()
    doc_in_db = db_session.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
    assert doc_in_db is not None
    assert doc_in_db.processing_status == "EXTRACTED"

    db_session.expire_all()
    entities_in_db = (
        db_session.query(ExtractedEntity)
        .filter(ExtractedEntity.document_id == uuid.UUID(doc_id))
        .all()
    )
    assert len(entities_in_db) > 0

    # Verify deterministic lab evaluation on extracted items
    abnormal_entities = [e for e in entities_in_db if e.is_abnormal]
    assert len(abnormal_entities) > 0
    for ab in abnormal_entities:
        assert ab.metadata_json.get("deterministic_flag") in ["HIGH", "LOW"]
        assert "is_abnormal = (value < low or value > high)" in ab.metadata_json.get("rule", "")

    # 4. Verify Audit Log was emitted
    audit_logs = (
        db_session.query(AuditLog)
        .filter(AuditLog.session_id == session.id)
        .all()
    )
    actions = [log.action for log in audit_logs]
    assert "document_uploaded" in actions
    assert "document_extracted" in actions


def test_document_list_and_entity_filtering(client: TestClient, db_session):
    patient = Patient(first_name="Bob", last_name="Marley", dob="1975-02-06", gender="male")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, mode="MODERN", lifecycle_status="IN_PROGRESS")
    db_session.add(session)
    db_session.commit()

    # Upload document
    img_content = b"\x89PNG\r\n\x1a\n glucose lab report scan"
    response = client.post(
        f"/api/v1/sessions/{session.id}/documents",
        files={"file": ("lab_scan.png", io.BytesIO(img_content), "image/png")},
    )
    assert response.status_code == 201
    doc_id = response.json()["id"]

    # Test GET /sessions/{id}/documents
    docs_resp = client.get(f"/api/v1/sessions/{session.id}/documents")
    assert docs_resp.status_code == 200
    docs_data = docs_resp.json()
    assert docs_data["total"] == 1
    assert docs_data["documents"][0]["id"] == doc_id

    # Test GET /sessions/{id}/documents/{doc_id}
    single_doc_resp = client.get(f"/api/v1/sessions/{session.id}/documents/{doc_id}")
    assert single_doc_resp.status_code == 200
    assert single_doc_resp.json()["filename"] == "lab_scan.png"

    # Test GET /sessions/{id}/entities
    entities_resp = client.get(f"/api/v1/sessions/{session.id}/entities")
    assert entities_resp.status_code == 200
    all_entities = entities_resp.json()["entities"]
    assert len(all_entities) > 0

    # Test GET /sessions/{id}/entities?abnormal_only=true
    abnormal_resp = client.get(f"/api/v1/sessions/{session.id}/entities?abnormal_only=true")
    assert abnormal_resp.status_code == 200
    abnormal_items = abnormal_resp.json()["entities"]
    assert all(item["is_abnormal"] is True for item in abnormal_items)


def test_document_delete_cascades_entities(client: TestClient, db_session):
    patient = Patient(first_name="Charlie", last_name="Brown", dob="1990-11-04", gender="male")
    db_session.add(patient)
    db_session.commit()

    session = Session(patient_id=patient.id, mode="MODERN", lifecycle_status="IN_PROGRESS")
    db_session.add(session)
    db_session.commit()

    # Upload document
    pdf_content = b"%PDF-1.4 prescription report"
    response = client.post(
        f"/api/v1/sessions/{session.id}/documents",
        files={"file": ("prescription.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    doc_id = uuid.UUID(response.json()["id"])

    # Verify entities exist
    assert db_session.query(ExtractedEntity).filter(ExtractedEntity.document_id == doc_id).count() > 0

    # Delete document
    del_resp = client.delete(f"/api/v1/sessions/{session.id}/documents/{doc_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Verify document and entities are removed
    assert db_session.query(Document).filter(Document.id == doc_id).first() is None
    assert db_session.query(ExtractedEntity).filter(ExtractedEntity.document_id == doc_id).count() == 0

    # Verify audit log for deletion
    delete_log = (
        db_session.query(AuditLog)
        .filter(AuditLog.session_id == session.id, AuditLog.action == "document_deleted")
        .first()
    )
    assert delete_log is not None
