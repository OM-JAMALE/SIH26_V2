from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InformationStatus(str, Enum):
    UNKNOWN = "UNKNOWN"  # Information not provided or not asked yet
    DENIED = "DENIED"    # Explicitly denied by patient
    PRESENT = "PRESENT"  # Explicitly confirmed / present


class SessionMode(str, Enum):
    MODERN = "MODERN"
    AYUSH = "AYUSH"


class SessionLifecycle(str, Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    SAFETY_ESCALATED = "SAFETY_ESCALATED"
    COMPLETED = "COMPLETED"


class InterviewState(str, Enum):
    IDENTIFICATION = "IDENTIFICATION"
    CHIEF_COMPLAINT = "CHIEF_COMPLAINT"
    HPI = "HPI"
    PAST_MEDICAL_HISTORY = "PAST_MEDICAL_HISTORY"
    PAST_SURGICAL_HISTORY = "PAST_SURGICAL_HISTORY"
    MEDICATIONS = "MEDICATIONS"
    ALLERGIES = "ALLERGIES"
    FAMILY_HISTORY = "FAMILY_HISTORY"
    PERSONAL_HISTORY = "PERSONAL_HISTORY"
    REVIEW_OF_SYSTEMS = "REVIEW_OF_SYSTEMS"
    COMPLETED = "COMPLETED"


class SocratesAttribute(str, Enum):
    SITE = "SITE"
    ONSET = "ONSET"
    CHARACTER = "CHARACTER"
    RADIATION = "RADIATION"
    ASSOCIATED_SYMPTOMS = "ASSOCIATED_SYMPTOMS"
    TIME_COURSE = "TIME_COURSE"
    EXACERBATING_RELIEVING_FACTORS = "EXACERBATING_RELIEVING_FACTORS"
    SEVERITY = "SEVERITY"
    COMPLETED = "COMPLETED"


# --- CLINICAL HISTORY DATA MODELS ---

class ChiefComplaintItem(BaseModel):
    symptom: str = Field(..., description="Symptom name")
    status: InformationStatus = Field(InformationStatus.PRESENT)
    duration: Optional[str] = Field(None, description="e.g. 2 hours")
    details: Optional[str] = Field(None)


class HPISocratesData(BaseModel):
    site: Optional[str] = Field(None, description="Exact location of symptom")
    onset: Optional[str] = Field(None, description="When and how it started")
    character: Optional[str] = Field(None, description="Nature e.g. pressure, sharp, dull")
    radiation: Optional[str] = Field(None, description="Where pain spreads")
    associated_symptoms: List[str] = Field(default_factory=list, description="Co-occurring symptoms")
    time_course: Optional[str] = Field(None, description="Constant vs episodic, progression")
    exacerbating_relieving_factors: Optional[str] = Field(None, description="What makes it better/worse")
    severity: Optional[int] = Field(None, description="Scale 0 to 10")


class MedicalHistoryItem(BaseModel):
    condition: str = Field(..., description="Condition name e.g. Hypertension")
    status: InformationStatus = Field(InformationStatus.PRESENT)
    diagnosed_year: Optional[str] = Field(None)
    details: Optional[str] = Field(None)


class SurgicalHistoryItem(BaseModel):
    procedure: str = Field(..., description="Procedure name e.g. Appendectomy")
    status: InformationStatus = Field(InformationStatus.PRESENT)
    year: Optional[str] = Field(None)
    details: Optional[str] = Field(None)


class MedicationItem(BaseModel):
    name: str = Field(..., description="Medication name")
    status: InformationStatus = Field(InformationStatus.PRESENT)
    dosage: Optional[str] = Field(None)
    frequency: Optional[str] = Field(None)


class AllergyItem(BaseModel):
    allergen: str = Field(..., description="Substance e.g. Penicillin")
    status: InformationStatus = Field(InformationStatus.PRESENT)
    reaction: Optional[str] = Field(None, description="e.g. Hives, Anaphylaxis")


class FamilyHistoryItem(BaseModel):
    condition: str = Field(..., description="Medical condition e.g. Diabetes")
    relation: Optional[str] = Field(None, description="e.g. Father, Mother")
    status: InformationStatus = Field(InformationStatus.PRESENT)


class PersonalHistoryItem(BaseModel):
    category: str = Field(..., description="e.g. Smoking, Alcohol, Diet, Sleep")
    status: InformationStatus = Field(InformationStatus.PRESENT)
    details: Optional[str] = Field(None)


class ReviewOfSystemsItem(BaseModel):
    system: str = Field(..., description="e.g. Cardiovascular, Respiratory")
    symptom: str = Field(..., description="Symptom name")
    status: InformationStatus = Field(InformationStatus.PRESENT)


class ClinicalHistory(BaseModel):
    chief_complaint: List[ChiefComplaintItem] = Field(default_factory=list)
    hpi_socrates: HPISocratesData = Field(default_factory=HPISocratesData)
    past_medical_history: List[MedicalHistoryItem] = Field(default_factory=list)
    past_surgical_history: List[SurgicalHistoryItem] = Field(default_factory=list)
    medications: List[MedicationItem] = Field(default_factory=list)
    allergies: List[AllergyItem] = Field(default_factory=list)
    family_history: List[FamilyHistoryItem] = Field(default_factory=list)
    personal_history: List[PersonalHistoryItem] = Field(default_factory=list)
    review_of_systems: List[ReviewOfSystemsItem] = Field(default_factory=list)


# --- STRUCTURED EXTRACTION RESPONSE MODEL ---

class StructuredExtraction(BaseModel):
    extracted_symptoms: List[ChiefComplaintItem] = Field(default_factory=list)
    denied_symptoms: List[str] = Field(default_factory=list, description="Symptoms explicitly denied by patient")
    socrates_updates: HPISocratesData = Field(default_factory=HPISocratesData)
    medical_history_updates: List[MedicalHistoryItem] = Field(default_factory=list)
    surgical_history_updates: List[SurgicalHistoryItem] = Field(default_factory=list)
    medication_updates: List[MedicationItem] = Field(default_factory=list)
    allergy_updates: List[AllergyItem] = Field(default_factory=list)
    family_history_updates: List[FamilyHistoryItem] = Field(default_factory=list)
    personal_history_updates: List[PersonalHistoryItem] = Field(default_factory=list)
    ros_updates: List[ReviewOfSystemsItem] = Field(default_factory=list)
    patient_inquired_diagnosis_or_treatment: bool = Field(
        False,
        description="True if patient asked for a medical diagnosis or prescription"
    )


# --- API REQUEST / RESPONSE SCHEMAS ---

class CreateSessionRequest(BaseModel):
    patient_id: str = Field(..., description="Patient UUID")
    mode: SessionMode = Field(SessionMode.MODERN, description="MODERN or AYUSH")
    disclaimer_acknowledged: bool = Field(False, description="Explicit disclaimer acknowledgement")


class AcknowledgeDisclaimerRequest(BaseModel):
    disclaimer_acknowledged: bool = Field(True, description="Must be true")


class SubmitResponseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw patient text response")


class SafetyAlertPayload(BaseModel):
    flagged: bool = Field(False)
    rule_id: Optional[str] = None
    severity: Optional[str] = None
    emergency_message: Optional[str] = None


class SessionStateResponse(BaseModel):
    session_id: str
    patient_id: str
    lifecycle_status: SessionLifecycle
    mode: SessionMode
    disclaimer_acknowledged: bool
    disclaimer_acknowledged_at: Optional[datetime] = None
    current_section: InterviewState
    socrates_state: Optional[SocratesAttribute] = None
    latest_question: str
    structured_history: ClinicalHistory
    safety: SafetyAlertPayload
    created_at: datetime
    updated_at: datetime


class TurnResponse(BaseModel):
    id: str
    session_id: str
    turn_index: int
    speaker: str
    content: str
    extracted_data: Dict[str, Any]
    safety_alerts: Dict[str, Any]
    section: str
    created_at: datetime


class ProcessResponseResult(BaseModel):
    session_id: str
    lifecycle_status: SessionLifecycle
    current_section: InterviewState
    socrates_state: Optional[SocratesAttribute] = None
    next_question: str
    structured_updates: Dict[str, Any]
    safety: SafetyAlertPayload
