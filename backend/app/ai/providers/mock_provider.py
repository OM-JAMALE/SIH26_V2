import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel
from app.ai.providers.base import BaseLLMProvider
from app.ai.schemas.summary import (
    ClinicalSummarySchema,
    ClinicalItem,
    MedicationItem,
    LabInvestigation,
    RedFlagItem,
    InformationStatus,
)
from app.modules.conversation.schemas import StructuredExtraction, ChiefComplaintItem, InformationStatus as ConvInfoStatus



T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(BaseLLMProvider):
    def generate_structured(
        self, prompt: str, system_prompt: str, schema_class: Type[T]
    ) -> T:
        # Trigger forced invalid response for testing validation + retry pipeline
        if "SIMULATE_INVALID_JSON_RESPONSE" in prompt:
            raise ValueError("Mock LLM generated malformed JSON string that failed parsing.")

        if "SIMULATE_SCHEMA_TYPE_ERROR" in prompt:
            # Return raw JSON dict with invalid types to trigger Pydantic ValidationError
            invalid_dict = {
                "session_id": 12345,  # Int instead of string
                "chief_complaint": "Invalid string instead of list of items",
                "generated_summary_text": None,
            }
            return schema_class.model_validate(invalid_dict)

        # Extract session_id from prompt if present
        session_id_match = re.search(r"session[_\s]*id[\"':\s]+([a-zA-Z0-9\-]+)", prompt, re.IGNORECASE)
        session_id = session_id_match.group(1) if session_id_match else "mock-session-uuid"



        # Handle StructuredExtraction schema for Module A
        if schema_class == StructuredExtraction:
            text_lower = prompt.lower()
            inquired = any(kw in text_lower for kw in ["what do i have", "diagnose me", "what should i take", "cure me", "what medicine"])
            ext = StructuredExtraction(patient_inquired_diagnosis_or_treatment=inquired)
            
            if "chest pain" in text_lower or "pain" in text_lower or "headache" in text_lower or "fever" in text_lower or "cough" in text_lower:
                s_name = "Chest pain" if "chest pain" in text_lower else ("Headache" if "headache" in text_lower else ("Fever" if "fever" in text_lower else "Cough"))
                status = ConvInfoStatus.DENIED if any(neg in text_lower for neg in ["no ", "don't have", "do not have", "denies"]) else ConvInfoStatus.PRESENT
                if status == ConvInfoStatus.DENIED:
                    ext.denied_symptoms.append(s_name)
                    ext.extracted_symptoms.append(ChiefComplaintItem(symptom=s_name, status=ConvInfoStatus.DENIED))
                else:
                    ext.extracted_symptoms.append(ChiefComplaintItem(symptom=s_name, status=ConvInfoStatus.PRESENT))

            
            return ext  # type: ignore

        # Check for red flags in prompt
        red_flags = []
        if "chest pain" in prompt.lower() or "red_flag" in prompt.lower():
            red_flags.append(
                RedFlagItem(
                    flag_name="CHEST_PAIN_ACUTE",
                    description="Acute chest discomfort reported. Rule out acute coronary syndrome.",
                    source="DETERMINISTIC_RULES_ENGINE",
                )
            )

        mock_summary = ClinicalSummarySchema(

            session_id=session_id,
            chief_complaint=[
                ClinicalItem(
                    name="Chest pain / pressure",
                    status=InformationStatus.KNOWN,
                    details="Retrosternal pressure rated 7/10 onset 2 hours ago radiating to left arm",
                )
            ],
            history_of_present_illness=[
                ClinicalItem(
                    name="Onset",
                    status=InformationStatus.KNOWN,
                    details="2 hours prior to presentation while at rest",
                ),
                ClinicalItem(
                    name="Shortness of breath",
                    status=InformationStatus.DENIED,
                    details="Patient explicitly denies dyspnea or breathlessness",
                ),
            ],
            associated_symptoms=[
                ClinicalItem(
                    name="Diaphoresis",
                    status=InformationStatus.KNOWN,
                    details="Mild sweating reported",
                ),
                ClinicalItem(
                    name="Nausea",
                    status=InformationStatus.DENIED,
                    details="Patient denies nausea or vomiting",
                ),
            ],
            relevant_positive_findings=[
                ClinicalItem(
                    name="Left arm radiation",
                    status=InformationStatus.KNOWN,
                    details="Pain radiates to inner aspect of left arm",
                )
            ],
            relevant_negative_findings=[
                ClinicalItem(
                    name="Shortness of breath",
                    status=InformationStatus.DENIED,
                    details="Explicitly denied",
                ),
                ClinicalItem(
                    name="Fever",
                    status=InformationStatus.DENIED,
                    details="Explicitly denied",
                ),
            ],
            past_medical_history=[
                ClinicalItem(
                    name="Hypertension",
                    status=InformationStatus.KNOWN,
                    details="Diagnosed 5 years ago, managed with medication",
                )
            ],
            past_surgical_history=[],
            medications=[
                MedicationItem(
                    name="Amlodipine",
                    status=InformationStatus.KNOWN,
                    dosage="5mg",
                    frequency="once daily",
                    route="oral",
                )
            ],
            allergies=[
                ClinicalItem(
                    name="Penicillin",
                    status=InformationStatus.DENIED,
                    details="No known drug allergies reported",
                )
            ],
            family_history=[
                ClinicalItem(
                    name="Coronary Artery Disease",
                    status=InformationStatus.KNOWN,
                    details="Father had MI at age 58",
                )
            ],
            personal_social_history=[
                ClinicalItem(
                    name="Smoking",
                    status=InformationStatus.DENIED,
                    details="Non-smoker",
                )
            ],
            review_of_systems=[
                ClinicalItem(
                    name="Cardiovascular",
                    status=InformationStatus.KNOWN,
                    details="Chest pressure and left arm radiation",
                ),
                ClinicalItem(
                    name="Respiratory",
                    status=InformationStatus.DENIED,
                    details="No cough, wheezing, or dyspnea",
                ),
            ],
            investigations=[
                LabInvestigation(
                    test_name="Troponin I",
                    status=InformationStatus.KNOWN,
                    value="0.04 ng/mL",
                    numeric_value=0.04,
                    unit="ng/mL",
                    reference_range="0.00 - 0.03 ng/mL",
                    is_abnormal=True,
                )
            ],
            abnormal_findings=[
                ClinicalItem(
                    name="Elevated Troponin I",
                    status=InformationStatus.KNOWN,
                    value="0.04 ng/mL",
                    numeric_value=0.04,
                    unit="ng/mL",
                    reference_range="0.00 - 0.03 ng/mL",
                    details="Slightly elevated troponin level requiring urgent physician evaluation",
                )
            ],
            red_flags=red_flags,
            information_gaps=[
                "Exact lipid panel values not provided",
                "Recent ECG baseline tracing not available",
            ],
            generated_summary_text=(
                "Patient presents with acute retrosternal chest pressure (7/10) onset 2 hours ago at rest with radiation to the left arm. "
                "Denies shortness of breath, fever, or nausea. History of hypertension treated with Amlodipine 5mg. "
                "Family history of CAD. Lab results indicate slightly elevated Troponin I (0.04 ng/mL). "
                "Deterministic safety rules flagged acute chest pain for urgent physician review."
            ),
        )

        if schema_class == ClinicalSummarySchema:
            return mock_summary  # type: ignore

        # Default model validation for other generic Pydantic schemas
        return schema_class.model_validate(mock_summary.model_dump())
