"""Deterministic red flag detection rules.

RED FLAGS ARE NOT LLM-BASED. All detection rules are hardcoded
deterministically for patient safety and reproducibility.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RedFlagSeverity(str, Enum):
    """Red flag severity levels."""
    CRITICAL = "CRITICAL"  # Immediate physician review required
    HIGH = "HIGH"  # Urgent physician review
    MEDIUM = "MEDIUM"  # Physician review within hours
    LOW = "LOW"  # Physician review routine


class RedFlagCategory(str, Enum):
    """Red flag categories."""
    CARDIOVASCULAR = "CARDIOVASCULAR"
    RESPIRATORY = "RESPIRATORY"
    NEUROLOGICAL = "NEUROLOGICAL"
    METABOLIC = "METABOLIC"
    INFECTIOUS = "INFECTIOUS"
    HEMORRHAGE = "HEMORRHAGE"
    TOXIC = "TOXIC"
    ALLERGIC = "ALLERGIC"
    PSYCHIATRIC = "PSYCHIATRIC"
    UNKNOWN = "UNKNOWN"


class RedFlag(BaseModel):
    """Detected red flag."""
    
    flag_id: str = Field(
        ...,
        description="Unique red flag identifier"
    )
    
    category: RedFlagCategory = Field(
        ...,
        description="Red flag category"
    )
    
    severity: RedFlagSeverity = Field(
        default=RedFlagSeverity.MEDIUM,
        description="Severity level"
    )
    
    rule_name: str = Field(
        ...,
        description="Name of triggered rule"
    )
    
    description: str = Field(
        ...,
        description="Description of red flag"
    )
    
    detected_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Values that triggered the rule"
    )
    
    recommended_action: str = Field(
        ...,
        description="Recommended action by physician"
    )
    
    requires_immediate_escalation: bool = Field(
        default=False,
        description="Whether escalation is required"
    )


class RedFlagDetector:
    """Deterministic red flag detection engine.
    
    ALL RULES ARE HARDCODED. Not LLM-based.
    Rules trigger on specific symptom combinations, vital signs, lab values, etc.
    """
    
    # Symptoms that trigger red flags
    CRITICAL_SYMPTOMS = {
        "chest pain": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.CARDIOVASCULAR},
        "acute chest pain": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.CARDIOVASCULAR},
        "shortness of breath": {"severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.RESPIRATORY},
        "difficulty breathing": {"severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.RESPIRATORY},
        "severe headache": {"severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.NEUROLOGICAL},
        "sudden severe headache": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.NEUROLOGICAL},
        "loss of consciousness": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.NEUROLOGICAL},
        "severe dizziness": {"severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.NEUROLOGICAL},
        "inability to speak": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.NEUROLOGICAL},
        "facial drooping": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.NEUROLOGICAL},
        "arm weakness": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.NEUROLOGICAL},
        "leg weakness": {"severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.NEUROLOGICAL},
        "severe allergic reaction": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.ALLERGIC},
        "anaphylaxis": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.ALLERGIC},
        "severe bleeding": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.HEMORRHAGE},
        "uncontrolled bleeding": {"severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.HEMORRHAGE},
        "blood in stool": {"severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.HEMORRHAGE},
        "blood in urine": {"severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.HEMORRHAGE},
        "severe abdominal pain": {"severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.UNKNOWN},
    }
    
    # Vital sign thresholds for red flags
    VITAL_SIGN_THRESHOLDS = {
        "systolic_bp_high": {"value": 180, "severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.CARDIOVASCULAR},
        "systolic_bp_low": {"value": 90, "severity": RedFlagSeverity.MEDIUM, "category": RedFlagCategory.CARDIOVASCULAR},
        "heart_rate_high": {"value": 120, "severity": RedFlagSeverity.MEDIUM, "category": RedFlagCategory.CARDIOVASCULAR},
        "heart_rate_low": {"value": 50, "severity": RedFlagSeverity.MEDIUM, "category": RedFlagCategory.CARDIOVASCULAR},
        "respiratory_rate_high": {"value": 30, "severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.RESPIRATORY},
        "temperature_high": {"value": 39.5, "severity": RedFlagSeverity.MEDIUM, "category": RedFlagCategory.INFECTIOUS},
        "oxygen_saturation_low": {"value": 90, "severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.RESPIRATORY},
    }
    
    # Lab value thresholds
    LAB_THRESHOLDS = {
        "troponin_elevated": {"value": 0.04, "severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.CARDIOVASCULAR},
        "potassium_high": {"value": 6.0, "severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.METABOLIC},
        "potassium_low": {"value": 3.0, "severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.METABOLIC},
        "glucose_critical_high": {"value": 400, "severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.METABOLIC},
        "glucose_critical_low": {"value": 50, "severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.METABOLIC},
        "hemoglobin_critical_low": {"value": 7, "severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.HEMORRHAGE},
        "plt_critical_low": {"value": 20, "severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.HEMORRHAGE},
        "creatinine_severe": {"value": 3.0, "severity": RedFlagSeverity.HIGH, "category": RedFlagCategory.METABOLIC},
        "inr_critical_high": {"value": 4.0, "severity": RedFlagSeverity.CRITICAL, "category": RedFlagCategory.HEMORRHAGE},
    }
    
    @staticmethod
    def detect_symptom_red_flags(symptom: str) -> Optional[RedFlag]:
        """Detect red flags from symptom keywords.
        
        Args:
            symptom: Patient-reported symptom
            
        Returns:
            RedFlag if symptom matches known red flag patterns, None otherwise
        """
        symptom_lower = symptom.lower().strip()
        
        # Check for exact matches
        if symptom_lower in RedFlagDetector.CRITICAL_SYMPTOMS:
            rule_info = RedFlagDetector.CRITICAL_SYMPTOMS[symptom_lower]
            return RedFlag(
                flag_id=f"SYMPTOM_{symptom_lower.replace(' ', '_').upper()}",
                category=rule_info["category"],
                severity=rule_info["severity"],
                rule_name="Critical symptom detected",
                description=f"Patient reported: {symptom}",
                detected_values={"symptom": symptom},
                recommended_action="Immediate physician evaluation required",
                requires_immediate_escalation=rule_info["severity"] in [
                    RedFlagSeverity.CRITICAL
                ]
            )
        
        # Check for partial matches
        for critical_symptom, rule_info in RedFlagDetector.CRITICAL_SYMPTOMS.items():
            if critical_symptom in symptom_lower or symptom_lower in critical_symptom:
                return RedFlag(
                    flag_id=f"SYMPTOM_{critical_symptom.replace(' ', '_').upper()}",
                    category=rule_info["category"],
                    severity=rule_info["severity"],
                    rule_name=f"Potential red flag: {critical_symptom}",
                    description=f"Patient reported: {symptom}",
                    detected_values={"symptom": symptom},
                    recommended_action="Physician review recommended",
                    requires_immediate_escalation=rule_info["severity"] == RedFlagSeverity.CRITICAL
                )
        
        return None
    
    @staticmethod
    def detect_vital_sign_red_flags(
        vital_name: str,
        value: float
    ) -> Optional[RedFlag]:
        """Detect red flags from vital signs.
        
        Args:
            vital_name: Name of vital sign (e.g., 'systolic_bp', 'heart_rate')
            value: Vital sign value
            
        Returns:
            RedFlag if vital sign is abnormal, None otherwise
        """
        # Check against thresholds
        for threshold_key, threshold_info in RedFlagDetector.VITAL_SIGN_THRESHOLDS.items():
            if vital_name.lower() in threshold_key:
                threshold_value = threshold_info["value"]
                is_abnormal = False
                
                # Check if it's a high threshold
                if "high" in threshold_key:
                    is_abnormal = value >= threshold_value
                elif "low" in threshold_key:
                    is_abnormal = value <= threshold_value
                
                if is_abnormal:
                    return RedFlag(
                        flag_id=f"VITAL_{vital_name.upper()}",
                        category=threshold_info["category"],
                        severity=threshold_info["severity"],
                        rule_name=f"Abnormal {vital_name}",
                        description=f"Vital sign {vital_name} = {value} (threshold: {threshold_value})",
                        detected_values={"vital_name": vital_name, "value": value, "threshold": threshold_value},
                        recommended_action="Physician review recommended",
                        requires_immediate_escalation=threshold_info["severity"] == RedFlagSeverity.CRITICAL
                    )
        
        return None
    
    @staticmethod
    def detect_lab_red_flags(
        test_name: str,
        value: float
    ) -> Optional[RedFlag]:
        """Detect red flags from lab values.
        
        Args:
            test_name: Name of lab test
            value: Lab value
            
        Returns:
            RedFlag if lab value is critical, None otherwise
        """
        test_name_lower = test_name.lower()
        
        # Check against lab thresholds
        for threshold_key, threshold_info in RedFlagDetector.LAB_THRESHOLDS.items():
            if threshold_key.split("_")[0] in test_name_lower or test_name_lower in threshold_key:
                threshold_value = threshold_info["value"]
                is_abnormal = False
                
                # Determine if abnormal
                if "high" in threshold_key or "elevated" in threshold_key:
                    is_abnormal = value >= threshold_value
                elif "low" in threshold_key or "critical" in threshold_key:
                    is_abnormal = value <= threshold_value
                
                if is_abnormal:
                    return RedFlag(
                        flag_id=f"LAB_{test_name.replace(' ', '_').upper()}",
                        category=threshold_info["category"],
                        severity=threshold_info["severity"],
                        rule_name=f"Critical {test_name}",
                        description=f"Lab result {test_name} = {value} (critical threshold: {threshold_value})",
                        detected_values={"test_name": test_name, "value": value, "threshold": threshold_value},
                        recommended_action="Immediate physician notification required",
                        requires_immediate_escalation=threshold_info["severity"] == RedFlagSeverity.CRITICAL
                    )
        
        return None
    
    @staticmethod
    def detect_combination_red_flags(
        symptoms: List[str],
        vitals: Optional[Dict[str, float]] = None,
        labs: Optional[Dict[str, float]] = None
    ) -> List[RedFlag]:
        """Detect red flags from combination of findings.
        
        Args:
            symptoms: List of reported symptoms
            vitals: Dict of vital signs
            labs: Dict of lab values
            
        Returns:
            List of detected red flags
        """
        flags = []
        
        # Check symptoms
        for symptom in symptoms:
            flag = RedFlagDetector.detect_symptom_red_flags(symptom)
            if flag:
                flags.append(flag)
        
        # Check vital signs
        if vitals:
            for vital_name, value in vitals.items():
                flag = RedFlagDetector.detect_vital_sign_red_flags(vital_name, value)
                if flag:
                    flags.append(flag)
        
        # Check lab values
        if labs:
            for test_name, value in labs.items():
                flag = RedFlagDetector.detect_lab_red_flags(test_name, value)
                if flag:
                    flags.append(flag)
        
        return flags
