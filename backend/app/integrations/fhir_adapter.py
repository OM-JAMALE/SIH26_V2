"""HL7 FHIR R4 Integration Adapter for Healthcare AI Platform.

Maps internal domain models (Session, ClinicalSummary, Documents) to HL7 FHIR R4 resources.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def to_fhir_diagnostic_report(
    session_id: str,
    patient_id: str,
    status: str = "final",
    category_code: str = "LAB",
    issued_at: Optional[str] = None,
    document_entries: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Convert a consultation session and associated documents to FHIR R4 DiagnosticReport.

    Args:
        session_id: Unique session identifier
        patient_id: Patient reference identifier
        status: DiagnosticReport status (registered | partial | preliminary | final)
        category_code: Diagnostic service section (LAB | RAD | OTH)
        issued_at: ISO timestamp of creation
        document_entries: List of extracted document metadata dictionaries

    Returns:
        FHIR R4 DiagnosticReport JSON structure
    """
    issued_timestamp = issued_at or datetime.now(timezone.utc).isoformat()
    presented_form = []

    if document_entries:
        for doc in document_entries:
            presented_form.append({
                "contentType": doc.get("mime_type", "application/pdf"),
                "title": doc.get("filename", "medical_record.pdf"),
                "size": doc.get("file_size", 0),
                "url": f"/api/v1/sessions/{session_id}/documents/{doc.get('id')}",
            })

    report = {
        "resourceType": "DiagnosticReport",
        "id": f"dr-{session_id}",
        "identifier": [
            {
                "system": "https://healthai.platform/diagnostic-reports",
                "value": session_id,
            }
        ],
        "status": status,
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": category_code,
                        "display": "Laboratory" if category_code == "LAB" else "Diagnostic Service",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": "Laboratory report",
                }
            ],
            "text": "Pre-consultation Digitized Laboratory & History Report",
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
            "type": "Patient",
        },
        "issued": issued_timestamp,
        "presentedForm": presented_form,
    }

    return report


def to_fhir_observation(
    summary_id: str,
    patient_id: str,
    observation_type: str,
    code_display: str,
    value: str,
    numeric_value: Optional[float] = None,
    unit: Optional[str] = None,
    reference_range: Optional[str] = None,
    is_abnormal: bool = False,
    issued_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert a structured clinical summary finding or lab result into a FHIR R4 Observation.

    Args:
        summary_id: Clinical summary reference ID
        patient_id: Patient ID
        observation_type: Category (vital-signs | laboratory | exam | social-history)
        code_display: Display name of symptom/lab test
        value: Textual value of observation
        numeric_value: Optional numeric quantity
        unit: Optional UCUM unit
        reference_range: Optional range description string
        is_abnormal: Whether deterministic rules flagged an abnormality
        issued_at: ISO timestamp

    Returns:
        FHIR R4 Observation JSON dictionary
    """
    timestamp = issued_at or datetime.now(timezone.utc).isoformat()
    interpretation_code = "A" if is_abnormal else "N"
    interpretation_display = "Abnormal" if is_abnormal else "Normal"

    observation: Dict[str, Any] = {
        "resourceType": "Observation",
        "id": f"obs-{summary_id}-{hash(code_display) & 0xffffffff}",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": observation_type,
                        "display": observation_type.capitalize(),
                    }
                ]
            }
        ],
        "code": {
            "text": code_display,
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
        },
        "effectiveDateTime": timestamp,
        "interpretation": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": interpretation_code,
                        "display": interpretation_display,
                    }
                ]
            }
        ],
    }

    if numeric_value is not None:
        observation["valueQuantity"] = {
            "value": numeric_value,
            "unit": unit or "",
            "system": "http://unitsofmeasure.org",
        }
    else:
        observation["valueString"] = value

    if reference_range:
        observation["referenceRange"] = [
            {
                "text": reference_range,
            }
        ]

    return observation
