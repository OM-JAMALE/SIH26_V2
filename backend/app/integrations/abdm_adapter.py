"""Ayushman Bharat Digital Mission (ABDM) Integration Adapter.

Provides HIP (Health Information Provider) payload creation and gateway mapping.
Fails gracefully to ensure external ABDM API connectivity issues do not block consultation workflows.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.core.logging import logger
from app.integrations.fhir_adapter import to_fhir_diagnostic_report, to_fhir_observation


def prepare_for_abdm(
    session_id: str,
    patient_id: str,
    abha_id: Optional[str] = None,
    summary_data: Optional[Dict[str, Any]] = None,
    documents_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Prepare ABDM-compliant Health Document Bundle payload.

    Args:
        session_id: Consultation session ID
        patient_id: Internal patient UUID
        abha_id: Ayushman Bharat Health Account ID (e.g. "91-1234-5678-9012")
        summary_data: Clinical summary data dict
        documents_data: List of uploaded document metadata dicts

    Returns:
        ABDM HIP compliant Health Document Bundle payload
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        target_abha = abha_id or f"ABHA-{patient_id[:8]}"

        # Construct FHIR DiagnosticReport resource
        fhir_report = to_fhir_diagnostic_report(
            session_id=session_id,
            patient_id=patient_id,
            status="final",
            issued_at=timestamp,
            document_entries=documents_data or [],
        )

        # Construct FHIR Observations for findings
        fhir_observations = []
        if summary_data and "structured_summary" in summary_data:
            st = summary_data["structured_summary"]
            # Map chief complaints
            for cc in st.get("chief_complaint", []):
                fhir_observations.append(
                    to_fhir_observation(
                        summary_id=summary_data.get("id", str(uuid.uuid4())),
                        patient_id=patient_id,
                        observation_type="exam",
                        code_display=cc.get("name", "Chief Complaint"),
                        value=cc.get("details", cc.get("status", "KNOWN")),
                        issued_at=timestamp,
                    )
                )
            # Map lab investigations
            for inv in st.get("investigations", []):
                fhir_observations.append(
                    to_fhir_observation(
                        summary_id=summary_data.get("id", str(uuid.uuid4())),
                        patient_id=patient_id,
                        observation_type="laboratory",
                        code_display=inv.get("test_name", "Lab Test"),
                        value=inv.get("value", ""),
                        numeric_value=inv.get("numeric_value"),
                        unit=inv.get("unit"),
                        reference_range=inv.get("reference_range"),
                        is_abnormal=inv.get("is_abnormal", False),
                        issued_at=timestamp,
                    )
                )

        bundle_id = f"abdm-bundle-{session_id}"
        abdm_payload = {
            "abdm_version": "v1.0",
            "hip_id": "HEALTH_AI_HIP_01",
            "consent_id": f"consent-{session_id}",
            "patient_health_info": {
                "abha_address": target_abha,
                "patient_id": patient_id,
                "session_id": session_id,
                "timestamp": timestamp,
            },
            "bundle": {
                "resourceType": "Bundle",
                "id": bundle_id,
                "type": "document",
                "timestamp": timestamp,
                "entry": [
                    {"resource": fhir_report},
                    *[{"resource": obs} for obs in fhir_observations],
                ],
            },
            "transfer_status": "READY_FOR_HIP_PUSH",
        }

        logger.info(f"✓ Successfully generated ABDM bundle for session {session_id}")
        return abdm_payload

    except Exception as ex:
        logger.error(f"⚠ Graceful failure during ABDM payload generation for session {session_id}: {ex}")
        # Fail gracefully: Return minimal fallback payload so caller application flow never crashes
        return {
            "abdm_version": "v1.0",
            "hip_id": "HEALTH_AI_HIP_01",
            "error": "ABDM payload generation degraded",
            "details": str(ex),
            "transfer_status": "DEGRADED_FALLBACK",
            "patient_health_info": {
                "patient_id": patient_id,
                "session_id": session_id,
            },
        }
