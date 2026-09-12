from typing import Optional
from pydantic import BaseModel, Field
from app.modules.conversation.schemas import InterviewState, SocratesAttribute, SessionMode, ClinicalHistory
from app.core.logging import logger


class DynamicQuestionResponse(BaseModel):
    question: str = Field(..., description="A concise, empathetic, dynamic clinical follow-up question for the patient.")


# Initial Disclaimer Text
INITIAL_DISCLAIMER_TEXT = (
    "Important Disclaimer: This tool collects health information to help prepare for a consultation with a qualified physician. "
    "It does not provide a medical diagnosis, treatment advice, or replace a healthcare professional. "
    "Do not rely on this system for emergency medical care."
)

# Emergency Escalation Message (Deterministic)
DETERMINISTIC_EMERGENCY_MESSAGE = (
    "CRITICAL ALERT: Your reported symptoms require immediate medical evaluation. "
    "This pre-consultation system cannot manage medical emergencies and chat input has been halted. "
    "Please seek emergency care immediately at the nearest emergency department or call emergency services (108 / 112)."
)

# Predefined response when patient asks for diagnosis or treatment advice
NO_DIAGNOSIS_TREATMENT_ADVICE_RESPONSE = (
    "I am an information gathering assistant helping prepare your pre-consultation summary. "
    "I am not authorized to provide medical diagnoses, treatment recommendations, or prescriptions. "
    "Your reporting clinician will review all history and provide diagnostic evaluation during your consultation."
)

# MODERN MODE QUESTION TEMPLATES (Fallbacks)
MODERN_QUESTIONS = {
    InterviewState.IDENTIFICATION: "Welcome. Before we begin, please confirm your full name and age.",
    InterviewState.CHIEF_COMPLAINT: "What is the main health concern or symptom that brings you in today?",
    InterviewState.HPI: "Could you tell me more about how your {symptom} has been developing?",
    
    # SOCRATES FLOW
    SocratesAttribute.SITE: "Could you clarify the main area or location of your {symptom}?",
    SocratesAttribute.ONSET: "When did this {symptom} first start, and was the onset sudden or gradual?",
    SocratesAttribute.CHARACTER: "How would you describe the sensation (e.g., sharp, dull ache, pressure, spinning, burning)?",
    SocratesAttribute.RADIATION: "Does the discomfort spread or radiate to any other area?",
    SocratesAttribute.ASSOCIATED_SYMPTOMS: "Are you experiencing any other symptoms along with the {symptom} (e.g., nausea, low energy)?",
    SocratesAttribute.TIME_COURSE: "Has the {symptom} been continuous since it started, or does it come and go in episodes?",
    SocratesAttribute.EXACERBATING_RELIEVING_FACTORS: "Is there anything specific that makes the {symptom} better or worse (e.g., rest, posture, movement)?",
    SocratesAttribute.SEVERITY: "On a scale from 0 to 10 (where 0 is no pain/discomfort and 10 is severe), how severe is it?",

    InterviewState.PAST_MEDICAL_HISTORY: "Do you have any diagnosed medical conditions (e.g. hypertension, diabetes, asthma)?",
    InterviewState.PAST_SURGICAL_HISTORY: "Have you ever had any surgeries or hospitalizations in the past?",
    InterviewState.MEDICATIONS: "Are you currently taking any prescription or over-the-counter medications?",
    InterviewState.ALLERGIES: "Do you have any known allergies to medications, foods, or environmental factors?",
    InterviewState.FAMILY_HISTORY: "Does anyone in your immediate family have a history of serious medical conditions (e.g. heart disease, diabetes)?",
    InterviewState.PERSONAL_HISTORY: "Do you smoke, drink alcohol, or have any specific diet/lifestyle habits we should note?",
    InterviewState.REVIEW_OF_SYSTEMS: "Is there any other system symptom (such as cough, rash, digestive issue) you would like to mention?",
    InterviewState.COMPLETED: "Thank you. Your pre-consultation history has been recorded and synthesized for physician review.",
}

# AYUSH MODE QUESTION TEMPLATES (Fallbacks)
AYUSH_QUESTIONS = {
    InterviewState.IDENTIFICATION: "Namaste. Before we begin the intake, please confirm your details.",
    InterviewState.CHIEF_COMPLAINT: "What primary discomfort or imbalance (Lakshana) brings you here today?",
    InterviewState.HPI: "Could you share how this imbalance ({symptom}) has progressed?",
    
    # SOCRATES FLOW IN AYUSH CONTEXT
    SocratesAttribute.SITE: "Which body region (Sthana) is predominantly affected by the {symptom}?",
    SocratesAttribute.ONSET: "When did this discomfort start, and was it linked to seasonal changes or diet?",
    SocratesAttribute.CHARACTER: "How would you describe the nature of this discomfort (e.g., dry, heavy, sharp, burning)?",
    SocratesAttribute.RADIATION: "Does the discomfort travel or shift to other regions?",
    SocratesAttribute.ASSOCIATED_SYMPTOMS: "Do you notice associated symptoms like altered appetite (Agni) or digestive changes?",
    SocratesAttribute.TIME_COURSE: "Is the discomfort worse at specific times of day, night, or after meals?",
    SocratesAttribute.EXACERBATING_RELIEVING_FACTORS: "What foods, activities, or weather conditions aggravate or soothe the discomfort?",
    SocratesAttribute.SEVERITY: "On a scale of 0 to 10, how severe is this imbalance affecting your daily routine?",

    InterviewState.PAST_MEDICAL_HISTORY: "Do you have any prior chronic conditions or long-standing health imbalances?",
    InterviewState.PAST_SURGICAL_HISTORY: "Have you undergone any previous surgical procedures or intensive therapies?",
    InterviewState.MEDICATIONS: "Are you currently taking any Ayurvedic, Herbal, or Allopathic medications?",
    InterviewState.ALLERGIES: "Do you have any sensitivities or allergic reactions to specific herbs, foods, or substances?",
    InterviewState.FAMILY_HISTORY: "Is there a history of health imbalances in your family?",
    InterviewState.PERSONAL_HISTORY: "Could you share details about your daily routine (Dinacharya), sleep (Nidra), and diet (Ahara)?",
    InterviewState.REVIEW_OF_SYSTEMS: "Are there any additional bodily observations (like digestion, bowel movements, energy) you wish to mention?",
    InterviewState.COMPLETED: "Thank you. Your comprehensive intake history is complete and ready for clinical review.",
}


def get_template_question(
    state: InterviewState,
    socrates_attr: Optional[SocratesAttribute] = None,
    mode: SessionMode = SessionMode.MODERN,
    symptom_name: Optional[str] = None,
) -> str:
    questions_map = AYUSH_QUESTIONS if mode == SessionMode.AYUSH else MODERN_QUESTIONS
    symptom = symptom_name or "symptom"

    if state == InterviewState.HPI and socrates_attr and socrates_attr != SocratesAttribute.COMPLETED:
        template = questions_map.get(socrates_attr, questions_map[InterviewState.HPI])
        return template.format(symptom=symptom)

    return questions_map.get(state, "Could you please elaborate further on your symptoms?")


def generate_ai_dynamic_question(
    provider,
    state: InterviewState,
    socrates_attr: Optional[SocratesAttribute],
    mode: SessionMode,
    history: ClinicalHistory,
    last_patient_input: str,
    patient_prior_history: Optional[str] = None,
) -> str:
    """Dynamically generate an empathetic, context-aware follow-up question via LLM (Gemini AI), incorporating past patient records."""
    # If mock provider or unavailable, use smart template fallback immediately
    if not provider or getattr(provider, "__class__", None).__name__ == "MockLLMProvider":
        primary_symptom = history.chief_complaint[0].symptom if history.chief_complaint else "symptom"
        return get_template_question(state, socrates_attr, mode, primary_symptom)

    chief_complaints_str = (
        ", ".join([c.symptom for c in history.chief_complaint if c.symptom])
        if history.chief_complaint
        else "Not stated yet"
    )

    system_prompt = (
        f"You are an empathetic, expert doctor conducting a pre-consultation clinical history intake.\n"
        f"Session Mode: {mode.value}\n"
        f"Target Intake Section: {state.value}\n"
        f"SOCRATES Sub-attribute to explore: {socrates_attr.value if socrates_attr else 'N/A'}\n\n"
        f"PATIENT PRIOR HISTORY ON FILE:\n"
        f"{patient_prior_history or 'First-time consultation (no prior records on file)'}\n\n"
        f"CRITICAL CLINICAL RULES:\n"
        f"1. Formulate ONE (1) natural, concise, and highly relevant follow-up question for section '{state.value}'.\n"
        f"2. HISTORY-AWARENESS: If the patient's prior medical history already answers a question (e.g. known hypertension, known asthma, or known allergies), DO NOT ask them again. Acknowledge them naturally instead.\n"
        f"3. NEVER ask generic or absurd questions that make no sense for the symptom. For example, if the symptom is 'dizziness' or 'headache', NEVER ask 'Where in your body do you feel dizziness?'. Instead, ask about duration, triggers, severity, or associated sensations naturally.\n"
        f"4. Do NOT provide medical diagnoses, treatment recommendations, or prescriptions.\n"
        f"5. Keep the question empathetic, professional, and brief (1 to 2 sentences max)."
    )

    user_prompt = (
        f"Patient's Extracted Complaints: {chief_complaints_str}\n"
        f"Patient's Latest Response: \"{last_patient_input}\"\n\n"
        f"Formulate the next follow-up question for section {state.value} ({socrates_attr.value if socrates_attr else ''})."
    )

    try:
        res = provider.generate_structured(user_prompt, system_prompt, DynamicQuestionResponse)
        if res and res.question and res.question.strip():
            return res.question.strip()
    except Exception as e:
        logger.warning(f"Dynamic AI question generation failed, using fallback: {e}")

    primary_symptom = history.chief_complaint[0].symptom if history.chief_complaint else "symptom"
    return get_template_question(state, socrates_attr, mode, primary_symptom)
