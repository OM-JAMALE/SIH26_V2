import re
from abc import ABC, abstractmethod
from typing import Optional
from app.modules.conversation.schemas import (
    StructuredExtraction,
    ChiefComplaintItem,
    HPISocratesData,
    MedicalHistoryItem,
    SurgicalHistoryItem,
    MedicationItem,
    AllergyItem,
    FamilyHistoryItem,
    PersonalHistoryItem,
    ReviewOfSystemsItem,
    InformationStatus,
)
from app.modules.conversation.prompts.extraction_prompts import build_extraction_prompt_v1
from app.ai.providers import get_llm_provider, BaseLLMProvider
from app.core.logging import logger


class BaseExtractionProvider(ABC):
    @abstractmethod
    def extract(
        self, text: str, current_section: str, socrates_state: str
    ) -> StructuredExtraction:
        pass


class MockExtractionProvider(BaseExtractionProvider):
    """Deterministic extraction provider for fast unit tests & offline mode."""

    def extract(
        self, text: str, current_section: str, socrates_state: str
    ) -> StructuredExtraction:
        text_lower = text.lower()
        res = StructuredExtraction()

        # Check for diagnosis or treatment advice inquiry
        if any(kw in text_lower for kw in ["what do i have", "diagnose me", "what should i take", "cure me", "what medicine"]):
            res.patient_inquired_diagnosis_or_treatment = True

        # Check for denied symptoms
        if any(neg in text_lower for neg in ["no ", "not ", "don't have", "do not have", "denies"]):
            for kw in ["fever", "cough", "shortness of breath", "chest pain", "nausea", "headache"]:
                if kw in text_lower and any(neg in text_lower for neg in ["no " + kw, "not have " + kw, "don't have " + kw, "do not have " + kw, "no "]):
                    res.denied_symptoms.append(kw)


        # Extraction logic based on section
        if current_section == "CHIEF_COMPLAINT" or "pain" in text_lower or "fever" in text_lower or "cough" in text_lower or "headache" in text_lower:
            symptom_name = "Chief complaint"
            if "chest pain" in text_lower:
                symptom_name = "Chest pain"
            elif "headache" in text_lower:
                symptom_name = "Headache"
            elif "cough" in text_lower:
                symptom_name = "Cough"
            elif "fever" in text_lower:
                symptom_name = "Fever"

            res.extracted_symptoms.append(
                ChiefComplaintItem(
                    symptom=symptom_name,
                    status=InformationStatus.PRESENT,
                    details=text,
                )
            )

        if current_section == "HPI":
            soc = HPISocratesData()
            if "left arm" in text_lower or "arm" in text_lower:
                soc.radiation = "Left arm"
            if "retrosternal" in text_lower or "chest" in text_lower or "head" in text_lower:
                soc.site = "Chest / Retrosternal" if "chest" in text_lower or "retrosternal" in text_lower else "Head"
            if "2 hours" in text_lower or "yesterday" in text_lower:
                soc.onset = "2 hours ago" if "2 hours" in text_lower else "Yesterday"
            if "pressure" in text_lower or "sharp" in text_lower or "throbbing" in text_lower:
                soc.character = "Pressure" if "pressure" in text_lower else "Sharp/Throbbing"
            if "sweating" in text_lower or "nausea" in text_lower:
                soc.associated_symptoms = ["Sweating"] if "sweating" in text_lower else ["Nausea"]
            if "walking" in text_lower or "rest" in text_lower:
                soc.exacerbating_relieving_factors = "Worse with walking" if "walking" in text_lower else "Relieved by rest"
            
            # Extract severity rating if number 0-10 present
            sev_match = re.search(r"\b([0-9]|10)\b", text_lower)
            if sev_match:
                soc.severity = int(sev_match.group(1))

            res.socrates_updates = soc

        if current_section == "PAST_MEDICAL_HISTORY" or "hypertension" in text_lower or "diabetes" in text_lower:
            if "no diabetes" not in text_lower and "don't have diabetes" not in text_lower:
                if "hypertension" in text_lower or "high blood pressure" in text_lower:
                    res.medical_history_updates.append(MedicalHistoryItem(condition="Hypertension", status=InformationStatus.PRESENT))
                if "diabetes" in text_lower:
                    res.medical_history_updates.append(MedicalHistoryItem(condition="Diabetes Mellitus", status=InformationStatus.PRESENT))

        if current_section == "MEDICATIONS" or "mg" in text_lower or "taking" in text_lower:
            if "amlodipine" in text_lower or "aspirin" in text_lower or "atorvastatin" in text_lower:
                med_name = "Amlodipine" if "amlodipine" in text_lower else ("Aspirin" if "aspirin" in text_lower else "Atorvastatin")
                res.medication_updates.append(MedicationItem(name=med_name, status=InformationStatus.PRESENT, dosage="5mg"))

        if current_section == "ALLERGIES" or "allergy" in text_lower or "penicillin" in text_lower:
            if "no allergies" in text_lower or "no known drug allergies" in text_lower:
                res.allergy_updates.append(AllergyItem(allergen="Allergies", status=InformationStatus.DENIED))
            elif "penicillin" in text_lower:
                res.allergy_updates.append(AllergyItem(allergen="Penicillin", status=InformationStatus.PRESENT, reaction="Hives"))

        return res


class LLMExtractionProvider(BaseExtractionProvider):
    """LLM provider wrapper executing versioned extraction prompt with bounded retries."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or get_llm_provider()

    def extract(
        self, text: str, current_section: str, socrates_state: str, max_retries: int = 2
    ) -> StructuredExtraction:
        system_prompt, user_prompt, _ = build_extraction_prompt_v1(
            patient_text=text,
            current_section=current_section,
            socrates_state=socrates_state,
        )

        last_exception = None
        for attempt in range(1, max_retries + 2):
            try:
                retry_prompt = user_prompt
                if attempt > 1 and last_exception:
                    retry_prompt += f"\n\nPREVIOUS ATTEMPT ERROR: {str(last_exception)}. Correct schema strictly."

                result = self.llm_provider.generate_structured(
                    prompt=retry_prompt,
                    system_prompt=system_prompt,
                    schema_class=StructuredExtraction,
                )
                return result
            except Exception as e:
                last_exception = e
                logger.warning(f"Extraction attempt {attempt} failed: {str(e)}")

        logger.error(f"Extraction retries exhausted: {str(last_exception)}. Fallback to MockExtractionProvider.")
        return MockExtractionProvider().extract(text, current_section, socrates_state)


def get_extraction_provider(provider_type: Optional[str] = None) -> BaseExtractionProvider:
    if provider_type == "mock":
        return MockExtractionProvider()
    return LLMExtractionProvider()
