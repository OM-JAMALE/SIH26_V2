import re
from typing import List, Optional
from app.modules.conversation.schemas import StructuredExtraction, InformationStatus, SafetyAlertPayload
from app.modules.conversation.questions import DETERMINISTIC_EMERGENCY_MESSAGE

NEGATION_PATTERNS = [
    r"\bno\s+",
    r"\bdenies\s+",
    r"\bwithout\s+",
    r"\bnot\s+",
    r"\bno\s+history\s+of\s+",
    r"\bnegative\s+for\s+",
]


class SafetyRule:
    def __init__(
        self,
        rule_id: str,
        description: str,
        keywords: List[str],
        severity: str = "CRITICAL",
    ):
        self.rule_id = rule_id
        self.description = description
        self.keywords = keywords
        self.severity = severity

    def _is_negated(self, text: str, kw: str) -> bool:
        text_lower = text.lower()
        for neg in NEGATION_PATTERNS:
            pattern = neg + r"[a-z\s]{0,20}" + re.escape(kw)
            if re.search(pattern, text_lower):
                return True
        return False

    def evaluate(self, raw_text: str, extraction: StructuredExtraction) -> bool:
        text_lower = raw_text.lower()
        
        # 1. Check extracted symptoms first: if explicitly DENIED, ignore
        for s in extraction.extracted_symptoms:
            if s.status == InformationStatus.DENIED:
                s_lower = s.symptom.lower()
                for kw in self.keywords:
                    if kw in s_lower:
                        return False

        # Check explicit denied_symptoms list in extraction
        for d in extraction.denied_symptoms:
            d_lower = d.lower()
            for kw in self.keywords:
                if kw in d_lower:
                    return False

        # 2. Check raw text keywords
        for kw in self.keywords:
            if kw in text_lower:
                # Check if negated in raw text
                if not self._is_negated(raw_text, kw):
                    return True

        return False


# DEFINITION OF CONSERVATIVE RED-FLAG RULES
RED_FLAG_RULES = [
    SafetyRule(
        rule_id="RULE_CHEST_PAIN_ACUTE",
        description="Acute retrosternal chest pain, heavy pressure, or pain radiating to left arm/jaw",
        keywords=["chest pain", "chest pressure", "retrosternal pain", "pain in my chest", "heart attack"],
        severity="CRITICAL",
    ),
    SafetyRule(
        rule_id="RULE_DYSPNEA_SEVERE",
        description="Severe difficulty breathing or acute dyspnea",
        keywords=["can't breathe", "cannot breathe", "gasping for air", "severe shortness of breath", "unable to breathe", "difficulty breathing"],
        severity="CRITICAL",
    ),
    SafetyRule(
        rule_id="RULE_LOSS_OF_CONSCIOUSNESS",
        description="Syncope, fainting, or loss of consciousness",
        keywords=["passed out", "fainted", "lost consciousness", "blacked out", "fainting"],
        severity="CRITICAL",
    ),
    SafetyRule(
        rule_id="RULE_NEUROLOGICAL_DEFICIT",
        description="Sudden weakness, facial droop, slurred speech, or stroke symptoms",
        keywords=["slurred speech", "facial droop", "sudden weakness", "arm numbness", "paralyzed", "stroke"],
        severity="CRITICAL",
    ),
    SafetyRule(
        rule_id="RULE_UNCONTROLLED_BLEEDING",
        description="Uncontrolled active hemorrhage or severe blood loss",
        keywords=["coughing blood", "vomiting blood", "uncontrolled bleeding", "gushing blood"],
        severity="CRITICAL",
    ),
    SafetyRule(
        rule_id="RULE_SEVERE_ALLERGY_ANAPHYLAXIS",
        description="Anaphylaxis, throat swelling, or severe airway allergy reaction",
        keywords=["throat closing", "throat is closing", "airway swelling", "anaphylaxis", "swollen tongue"],
        severity="CRITICAL",
    ),

    SafetyRule(
        rule_id="RULE_SUICIDAL_SELF_HARM",
        description="Suicidal ideation or self-harm statements",
        keywords=["suicide", "want to die", "kill myself", "end my life", "self harm"],
        severity="CRITICAL",
    ),
]


class SafetyRulesEngine:
    def __init__(self, rules: Optional[List[SafetyRule]] = None):
        self.rules = rules or RED_FLAG_RULES

    def evaluate_safety(
        self, raw_text: str, extraction: StructuredExtraction
    ) -> SafetyAlertPayload:
        """Evaluates patient text and extractions deterministically against red-flag rules."""
        for rule in self.rules:
            if rule.evaluate(raw_text, extraction):
                return SafetyAlertPayload(
                    flagged=True,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    emergency_message=DETERMINISTIC_EMERGENCY_MESSAGE,
                )

        return SafetyAlertPayload(flagged=False)
