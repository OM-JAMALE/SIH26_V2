from typing import Tuple, Optional, Dict, Any
from app.modules.conversation.schemas import (
    InterviewState,
    SocratesAttribute,
    SessionLifecycle,
    ClinicalHistory,
    StructuredExtraction,
    InformationStatus,
)


class InterviewStateMachine:
    """Deterministic, pure-logic interview state transition machine."""

    SOCRATES_ORDER = [
        SocratesAttribute.SITE,
        SocratesAttribute.ONSET,
        SocratesAttribute.CHARACTER,
        SocratesAttribute.RADIATION,
        SocratesAttribute.ASSOCIATED_SYMPTOMS,
        SocratesAttribute.TIME_COURSE,
        SocratesAttribute.EXACERBATING_RELIEVING_FACTORS,
        SocratesAttribute.SEVERITY,
    ]

    SECTION_ORDER = [
        InterviewState.IDENTIFICATION,
        InterviewState.CHIEF_COMPLAINT,
        InterviewState.HPI,
        InterviewState.PAST_MEDICAL_HISTORY,
        InterviewState.PAST_SURGICAL_HISTORY,
        InterviewState.MEDICATIONS,
        InterviewState.ALLERGIES,
        InterviewState.FAMILY_HISTORY,
        InterviewState.PERSONAL_HISTORY,
        InterviewState.REVIEW_OF_SYSTEMS,
        InterviewState.COMPLETED,
    ]

    def advance_state(
        self,
        current_state: InterviewState,
        current_socrates: Optional[SocratesAttribute],
        history: ClinicalHistory,
        extraction: StructuredExtraction,
    ) -> Tuple[InterviewState, Optional[SocratesAttribute], SessionLifecycle]:
        """Determines the next (state, socrates_attribute, lifecycle_status) deterministically."""

        # 1. If currently in IDENTIFICATION -> move to CHIEF_COMPLAINT
        if current_state == InterviewState.IDENTIFICATION:
            return InterviewState.CHIEF_COMPLAINT, SocratesAttribute.SITE, SessionLifecycle.IN_PROGRESS

        # 2. If currently in CHIEF_COMPLAINT -> move to HPI (SOCRATES SITE)
        if current_state == InterviewState.CHIEF_COMPLAINT:
            return InterviewState.HPI, SocratesAttribute.SITE, SessionLifecycle.IN_PROGRESS

        # 3. If currently in HPI -> progress through SOCRATES flow
        if current_state == InterviewState.HPI:
            next_soc = self._next_socrates_attribute(current_socrates, history)
            if next_soc == SocratesAttribute.COMPLETED:
                # Move to next major section: PAST_MEDICAL_HISTORY
                return InterviewState.PAST_MEDICAL_HISTORY, None, SessionLifecycle.IN_PROGRESS
            return InterviewState.HPI, next_soc, SessionLifecycle.IN_PROGRESS

        # 4. Standard linear section progression for remaining history sections
        try:
            curr_idx = self.SECTION_ORDER.index(current_state)
            if curr_idx + 1 < len(self.SECTION_ORDER):
                next_state = self.SECTION_ORDER[curr_idx + 1]
                lifecycle = SessionLifecycle.COMPLETED if next_state == InterviewState.COMPLETED else SessionLifecycle.IN_PROGRESS
                return next_state, None, lifecycle
        except ValueError:
            pass

        return InterviewState.COMPLETED, None, SessionLifecycle.COMPLETED

    def _next_socrates_attribute(
        self,
        current_socrates: Optional[SocratesAttribute],
        history: ClinicalHistory,
    ) -> SocratesAttribute:
        if not current_socrates:
            return SocratesAttribute.SITE

        try:
            curr_idx = self.SOCRATES_ORDER.index(current_socrates)
            if curr_idx + 1 < len(self.SOCRATES_ORDER):
                return self.SOCRATES_ORDER[curr_idx + 1]
        except ValueError:
            pass

        return SocratesAttribute.COMPLETED


def update_clinical_history(
    history: ClinicalHistory, extraction: StructuredExtraction
) -> ClinicalHistory:
    """Merges structured extraction findings into accumulated ClinicalHistory with strict deduplication."""
    # 1. Chief Complaint Deduplication
    if extraction.extracted_symptoms:
        existing_symptoms = {
            c.symptom.lower().strip()
            for c in history.chief_complaint
            if getattr(c, "symptom", None)
        }
        for item in extraction.extracted_symptoms:
            sym_name = getattr(item, "symptom", None) or getattr(item, "name", None)
            if sym_name and sym_name.lower().strip() not in existing_symptoms:
                history.chief_complaint.append(item)
                existing_symptoms.add(sym_name.lower().strip())

    # 2. SOCRATES updates
    soc_up = extraction.socrates_updates
    if soc_up.site:
        history.hpi_socrates.site = soc_up.site
    if soc_up.onset:
        history.hpi_socrates.onset = soc_up.onset
    if soc_up.character:
        history.hpi_socrates.character = soc_up.character
    if soc_up.radiation:
        history.hpi_socrates.radiation = soc_up.radiation
    if soc_up.associated_symptoms:
        existing_assoc = {s.lower().strip() for s in history.hpi_socrates.associated_symptoms if isinstance(s, str)}
        for s in soc_up.associated_symptoms:
            if isinstance(s, str) and s.lower().strip() not in existing_assoc:
                history.hpi_socrates.associated_symptoms.append(s)
                existing_assoc.add(s.lower().strip())
    if soc_up.time_course:
        history.hpi_socrates.time_course = soc_up.time_course
    if soc_up.exacerbating_relieving_factors:
        history.hpi_socrates.exacerbating_relieving_factors = soc_up.exacerbating_relieving_factors
    if soc_up.severity is not None:
        history.hpi_socrates.severity = soc_up.severity

    # 3. Medical History Deduplication
    if extraction.medical_history_updates:
        existing_med_hist = {
            m.condition.lower().strip() for m in history.past_medical_history if getattr(m, "condition", None)
        }
        for item in extraction.medical_history_updates:
            cond = getattr(item, "condition", None)
            if cond and cond.lower().strip() not in existing_med_hist:
                history.past_medical_history.append(item)
                existing_med_hist.add(cond.lower().strip())

    # 4. Surgical History Deduplication
    if extraction.surgical_history_updates:
        existing_surg = {
            s.procedure.lower().strip() for s in history.past_surgical_history if getattr(s, "procedure", None)
        }
        for item in extraction.surgical_history_updates:
            proc = getattr(item, "procedure", None)
            if proc and proc.lower().strip() not in existing_surg:
                history.past_surgical_history.append(item)
                existing_surg.add(proc.lower().strip())

    # 5. Medications Deduplication
    if extraction.medication_updates:
        existing_meds = {
            m.name.lower().strip() for m in history.medications if getattr(m, "name", None)
        }
        for item in extraction.medication_updates:
            m_name = getattr(item, "name", None)
            if m_name and m_name.lower().strip() not in existing_meds:
                history.medications.append(item)
                existing_meds.add(m_name.lower().strip())

    # 6. Allergies Deduplication
    if extraction.allergy_updates:
        existing_allergies = {
            a.allergen.lower().strip() for a in history.allergies if getattr(a, "allergen", None)
        }
        for item in extraction.allergy_updates:
            alg = getattr(item, "allergen", None)
            if alg and alg.lower().strip() not in existing_allergies:
                history.allergies.append(item)
                existing_allergies.add(alg.lower().strip())

    # 7. Family History Deduplication
    if extraction.family_history_updates:
        history.family_history.extend(extraction.family_history_updates)

    # 8. Personal History Deduplication
    if extraction.personal_history_updates:
        history.personal_history.extend(extraction.personal_history_updates)

    # 9. Review of Systems Deduplication
    if extraction.ros_updates:
        history.review_of_systems.extend(extraction.ros_updates)

    return history
