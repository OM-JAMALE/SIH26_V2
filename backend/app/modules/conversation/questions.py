from typing import Optional
from app.modules.conversation.schemas import InterviewState, SocratesAttribute, SessionMode

# Initial Disclaimer Text
INITIAL_DISCLAIMER_TEXT = (
    "Important Disclaimer: This tool collects health information to help prepare for a consultation with a qualified physician. "
    "It does not provide a medical diagnosis, treatment advice, or replace a healthcare professional. "
    "Do not rely on this system for emergency medical care."
)

# Emergency Escalation Message (Deterministic)
DETERMINISTIC_EMERGENCY_MESSAGE = (
    "CRITICAL ALERT: Your reported symptoms may require urgent medical attention. "
    "This system is an information collection tool and cannot assess or manage medical emergencies. "
    "Please seek immediate medical care at the nearest emergency department or call emergency medical services (e.g. 108 / 112)."
)

# Predefined response when patient asks for diagnosis or treatment advice
NO_DIAGNOSIS_TREATMENT_ADVICE_RESPONSE = (
    "I am an information gathering assistant helping prepare your pre-consultation summary. "
    "I am not authorized to provide medical diagnoses, treatment recommendations, or prescriptions. "
    "Your reporting clinician will review all history and provide diagnostic evaluation during your consultation."
)

# MODERN MODE QUESTION TEMPLATES
MODERN_QUESTIONS = {
    InterviewState.IDENTIFICATION: "Welcome. Before we begin, please confirm your full name and age.",
    InterviewState.CHIEF_COMPLAINT: "What is the main health concern or symptom that brings you in today?",
    InterviewState.HPI: "Could you tell me more about how your {symptom} has been developing?",
    
    # SOCRATES FLOW
    SocratesAttribute.SITE: "Where exactly in your body do you feel the {symptom}?",
    SocratesAttribute.ONSET: "When did this {symptom} first start, and was the onset sudden or gradual?",
    SocratesAttribute.CHARACTER: "How would you describe the sensation or pain (e.g., sharp, dull ache, pressure, burning)?",
    SocratesAttribute.RADIATION: "Does the pain or discomfort spread or radiate to any other part of your body?",
    SocratesAttribute.ASSOCIATED_SYMPTOMS: "Are you experiencing any other symptoms along with the {symptom} (e.g., sweating, dizziness)?",
    SocratesAttribute.TIME_COURSE: "Has the {symptom} been continuous since it started, or does it come and go in episodes?",
    SocratesAttribute.EXACERBATING_RELIEVING_FACTORS: "Is there anything specific that makes the {symptom} better or worse (e.g., rest, movement, eating)?",
    SocratesAttribute.SEVERITY: "On a scale from 0 to 10 (where 0 is no pain and 10 is the worst imaginable pain), how severe is it?",

    InterviewState.PAST_MEDICAL_HISTORY: "Do you have any diagnosed medical conditions (e.g. hypertension, diabetes, asthma)?",
    InterviewState.PAST_SURGICAL_HISTORY: "Have you ever had any surgeries or hospitalizations in the past?",
    InterviewState.MEDICATIONS: "Are you currently taking any prescription or over-the-counter medications?",
    InterviewState.ALLERGIES: "Do you have any known allergies to medications, foods, or environmental factors?",
    InterviewState.FAMILY_HISTORY: "Does anyone in your immediate family have a history of serious medical conditions (e.g. heart disease, diabetes)?",
    InterviewState.PERSONAL_HISTORY: "Do you smoke, drink alcohol, or have any specific diet/lifestyle habits we should note?",
    InterviewState.REVIEW_OF_SYSTEMS: "Is there any other system symptom (such as cough, rash, digestive issue) you would like to mention?",
    InterviewState.COMPLETED: "Thank you. Your pre-consultation history has been recorded and synthesized for physician review.",
}

# AYUSH MODE QUESTION TEMPLATES
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
