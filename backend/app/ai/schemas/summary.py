from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class InformationStatus(str, Enum):
    KNOWN = "KNOWN"
    DENIED = "DENIED"
    NOT_PROVIDED = "NOT_PROVIDED"


class ClinicalItem(BaseModel):
    name: str = Field(..., description="Name of the symptom, condition, or finding")
    status: InformationStatus = Field(
        InformationStatus.KNOWN,
        description="Explicit status: KNOWN (present), DENIED (explicitly absent), NOT_PROVIDED (unknown/not asked)"
    )
    details: Optional[str] = Field(None, description="Detailed description or context")
    value: Optional[str] = Field(None, description="Textual value if applicable")
    numeric_value: Optional[float] = Field(None, description="Exact numerical value if applicable")
    unit: Optional[str] = Field(None, description="Measurement unit if applicable")
    reference_range: Optional[str] = Field(None, description="Reference range if applicable")


class MedicationItem(BaseModel):
    name: str = Field(..., description="Medication or drug name")
    status: InformationStatus = Field(
        InformationStatus.KNOWN,
        description="Explicit status: KNOWN (currently taking), DENIED (explicitly not taking), NOT_PROVIDED (unknown)"
    )
    dosage: Optional[str] = Field(None, description="Dosage e.g. 20mg")
    frequency: Optional[str] = Field(None, description="Frequency e.g. once daily")
    route: Optional[str] = Field(None, description="Route e.g. oral")


class LabInvestigation(BaseModel):
    test_name: str = Field(..., description="Laboratory test or investigation name")
    status: InformationStatus = Field(
        InformationStatus.KNOWN,
        description="Status: KNOWN, DENIED, NOT_PROVIDED"
    )
    value: Optional[str] = Field(None, description="Result value string")
    numeric_value: Optional[float] = Field(None, description="Exact numeric result")
    unit: Optional[str] = Field(None, description="Unit e.g. mg/dL")
    reference_range: Optional[str] = Field(None, description="Standard reference range")
    is_abnormal: Optional[bool] = Field(None, description="Deterministic abnormality flag")


class RedFlagItem(BaseModel):
    flag_name: str = Field(..., description="Red flag or clinical alert title")
    description: str = Field(..., description="Description of detected red flag")
    source: str = Field("DETERMINISTIC_RULES_ENGINE", description="Source of alert")


class ClinicalSummarySchema(BaseModel):
    session_id: str = Field(..., description="Session UUID identifier")
    chief_complaint: List[ClinicalItem] = Field(default_factory=list, description="Chief complaints")
    history_of_present_illness: List[ClinicalItem] = Field(default_factory=list, description="HPI findings including SOCRATES attributes")
    associated_symptoms: List[ClinicalItem] = Field(default_factory=list, description="Associated symptoms")
    relevant_positive_findings: List[ClinicalItem] = Field(default_factory=list, description="Positive clinical findings")
    relevant_negative_findings: List[ClinicalItem] = Field(default_factory=list, description="Explicitly denied negative findings")
    past_medical_history: List[ClinicalItem] = Field(default_factory=list, description="Past medical history")
    past_surgical_history: List[ClinicalItem] = Field(default_factory=list, description="Past surgical history")
    medications: List[MedicationItem] = Field(default_factory=list, description="Current or past medications")
    allergies: List[ClinicalItem] = Field(default_factory=list, description="Allergies and adverse reactions")
    family_history: List[ClinicalItem] = Field(default_factory=list, description="Family medical history")
    personal_social_history: List[ClinicalItem] = Field(default_factory=list, description="Personal and social history")
    review_of_systems: List[ClinicalItem] = Field(default_factory=list, description="Review of systems")
    investigations: List[LabInvestigation] = Field(default_factory=list, description="Lab tests and imaging")
    abnormal_findings: List[ClinicalItem] = Field(default_factory=list, description="Highlighted abnormal findings")
    red_flags: List[RedFlagItem] = Field(default_factory=list, description="Preserved red flags from safety engine")
    information_gaps: List[str] = Field(default_factory=list, description="Explicitly missing or unknown information items")
    generated_summary_text: str = Field(..., description="Synthesized non-diagnostic narrative overview")
