"""Unit and integration tests for Phase 7: Healthcare Integrations & Privacy Audit Logging."""

import uuid
import pytest
from app.integrations import (
    to_fhir_diagnostic_report,
    to_fhir_observation,
    log_consent_action,
    get_audit_trail,
    prepare_for_abdm,
)
from app.core.audit import log_audit_event, sanitize_details
from app.db.models.audit_log import AuditLog
from app.db.models.consent import Consent


def test_fhir_diagnostic_report_conversion():
    session_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())
    docs = [
        {"id": "doc-1", "filename": "blood_test.pdf", "mime_type": "application/pdf", "file_size": 1024}
    ]

    report = to_fhir_diagnostic_report(
        session_id=session_id,
        patient_id=patient_id,
        status="final",
        category_code="LAB",
        document_entries=docs,
    )

    assert report["resourceType"] == "DiagnosticReport"
    assert report["id"] == f"dr-{session_id}"
    assert report["status"] == "final"
    assert report["subject"]["reference"] == f"Patient/{patient_id}"
    assert len(report["presentedForm"]) == 1
    assert report["presentedForm"][0]["title"] == "blood_test.pdf"


def test_fhir_observation_conversion():
    summary_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())

    obs = to_fhir_observation(
        summary_id=summary_id,
        patient_id=patient_id,
        observation_type="laboratory",
        code_display="Hemoglobin",
        value="10.5",
        numeric_value=10.5,
        unit="g/dL",
        reference_range="12.0 - 16.0",
        is_abnormal=True,
    )

    assert obs["resourceType"] == "Observation"
    assert obs["subject"]["reference"] == f"Patient/{patient_id}"
    assert obs["code"]["text"] == "Hemoglobin"
    assert obs["valueQuantity"]["value"] == 10.5
    assert obs["valueQuantity"]["unit"] == "g/dL"
    assert obs["interpretation"][0]["coding"][0]["code"] == "A"
    assert obs["interpretation"][0]["coding"][0]["display"] == "Abnormal"


def test_consent_manager_flow(db_session):
    session_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    # Log grant action
    consent_grant = log_consent_action(
        db=db_session,
        session_id=session_id,
        patient_id=patient_id,
        purpose="Pre-consultation clinical trial",
        granted=True,
        terms_version="v1.0",
        ip_address="192.168.1.1",
    )

    assert consent_grant.granted is True
    assert consent_grant.patient_id == patient_id
    assert consent_grant.granted_at is not None

    # Retrieve audit trail
    trail = get_audit_trail(db=db_session, patient_id=patient_id)
    assert len(trail) >= 1
    assert trail[0]["granted"] is True
    assert trail[0]["terms_version"] == "v1.0"

    # Log revoke action
    consent_revoke = log_consent_action(
        db=db_session,
        session_id=session_id,
        patient_id=patient_id,
        granted=False,
    )
    assert consent_revoke.granted is False
    assert consent_revoke.revoked_at is not None


def test_abdm_payload_generation():
    session_id = str(uuid.uuid4())
    patient_id = str(uuid.uuid4())
    summary_data = {
        "id": str(uuid.uuid4()),
        "structured_summary": {
            "chief_complaint": [{"name": "Fever", "details": "High grade fever"}],
            "investigations": [
                {
                    "test_name": "Platelets",
                    "value": "110000",
                    "numeric_value": 110000.0,
                    "unit": "/uL",
                    "reference_range": "150000 - 450000",
                    "is_abnormal": True,
                }
            ],
        },
    }

    abdm_payload = prepare_for_abdm(
        session_id=session_id,
        patient_id=patient_id,
        abha_id="91-1234-5678-9012",
        summary_data=summary_data,
    )

    assert abdm_payload["abdm_version"] == "v1.0"
    assert abdm_payload["transfer_status"] == "READY_FOR_HIP_PUSH"
    assert abdm_payload["patient_health_info"]["abha_address"] == "91-1234-5678-9012"
    assert abdm_payload["bundle"]["resourceType"] == "Bundle"
    assert len(abdm_payload["bundle"]["entry"]) == 3  # 1 report + 2 observations


def test_privacy_audit_logging_redaction(db_session):
    session_id = uuid.uuid4()

    untrusted_details = {
        "action_name": "GENERATE_SUMMARY",
        "patient_text": "Patient complains of severe chest pain and breathlessness.",
        "clinical_text": "ECG shows ST elevation in leads V1-V4.",
        "llm_output": "Possible acute anterior wall myocardial infarction.",
        "api_key": "sk-proj-secret-123456789",
        "jwt_token": "bearer-xyz-secret",
        "non_sensitive_metric": 42,
        "status_flag": "SUCCESS",
    }

    audit = log_audit_event(
        db=db_session,
        action="SUMMARY_GENERATE",
        resource="clinical_summary",
        status="SUCCESS",
        session_id=session_id,
        user_id="doc-99",
        details=untrusted_details,
    )

    saved_log = db_session.query(AuditLog).filter(AuditLog.id == audit.id).first()

    assert saved_log is not None
    assert saved_log.action == "SUMMARY_GENERATE"
    assert saved_log.details["patient_text"] == "[REDACTED_CLINICAL_CONTENT]"
    assert saved_log.details["clinical_text"] == "[REDACTED_CLINICAL_CONTENT]"
    assert saved_log.details["llm_output"] == "[REDACTED_CLINICAL_CONTENT]"
    assert saved_log.details["api_key"] == "[REDACTED_CREDENTIAL]"
    assert saved_log.details["jwt_token"] == "[REDACTED_CREDENTIAL]"
    assert saved_log.details["non_sensitive_metric"] == 42
    assert saved_log.details["status_flag"] == "SUCCESS"
