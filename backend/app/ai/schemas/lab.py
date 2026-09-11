"""Lab and clinical abnormality schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SeverityEnum(str, Enum):
    """Clinical severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LabAbnormalitySchema(BaseModel):
    """Schema for lab abnormality detection.
    
    Uses deterministic rules (hardcoded reference ranges), not LLM.
    Abnormality is calculated as: value < low_range OR value > high_range
    """
    
    test_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of laboratory test"
    )
    
    value: float = Field(
        ...,
        description="Numeric test result value"
    )
    
    unit: str = Field(
        default="",
        description="Unit of measurement (e.g., mg/dL, mmol/L)"
    )
    
    normal_range: str = Field(
        ...,
        description="Normal reference range as string (e.g., '70-99', '<200', '>40')"
    )
    
    normal_range_low: Optional[float] = Field(
        None,
        description="Low boundary of normal range"
    )
    
    normal_range_high: Optional[float] = Field(
        None,
        description="High boundary of normal range"
    )
    
    is_abnormal: bool = Field(
        default=False,
        description="Whether value is abnormal (deterministic)"
    )
    
    severity: SeverityEnum = Field(
        default=SeverityEnum.LOW,
        description="Severity level: LOW, MEDIUM, HIGH, CRITICAL"
    )
    
    deviation_percentage: Optional[float] = Field(
        None,
        description="Percentage deviation from normal range (positive = high, negative = low)"
    )
    
    interpretation: Optional[str] = Field(
        None,
        max_length=500,
        description="Clinical interpretation of result"
    )
    
    risk_indicators: Optional[list[str]] = Field(
        None,
        description="Associated health risks"
    )
    
    @field_validator("test_name")
    @classmethod
    def validate_test_name(cls, v: str) -> str:
        """Ensure test name is not empty."""
        if not v or not v.strip():
            raise ValueError("Test name cannot be empty")
        return v.strip()
    
    @field_validator("normal_range")
    @classmethod
    def validate_normal_range(cls, v: str) -> str:
        """Ensure normal range string is not empty."""
        if not v or not v.strip():
            raise ValueError("Normal range cannot be empty")
        return v.strip()
    
    @field_validator("severity")
    @classmethod
    def validate_severity_with_abnormality(cls, v: SeverityEnum, info) -> SeverityEnum:
        """Ensure severity is only set for abnormal results."""
        if info.data.get("is_abnormal") is False and v != SeverityEnum.LOW:
            # Allow severity only if is_abnormal is True
            pass
        return v
    
    def calculate_abnormality(self) -> bool:
        """Calculate abnormality based on hardcoded deterministic rules.
        
        Rules:
        - If value < low_range: abnormal
        - If value > high_range: abnormal
        - Otherwise: normal
        
        Returns:
            True if abnormal, False if normal
        """
        if self.normal_range_low is not None and self.value < self.normal_range_low:
            return True
        if self.normal_range_high is not None and self.value > self.normal_range_high:
            return True
        return False
    
    def calculate_severity(self) -> SeverityEnum:
        """Calculate severity level based on deviation from normal range.
        
        Rules (deterministic):
        - <-50% or >+50% from range: CRITICAL
        - <-25% or >+25% from range: HIGH
        - <-10% or >+10% from range: MEDIUM
        - Otherwise: LOW
        
        Returns:
            Severity level
        """
        if not self.is_abnormal:
            return SeverityEnum.LOW
        
        if self.deviation_percentage is None:
            return SeverityEnum.MEDIUM
        
        abs_deviation = abs(self.deviation_percentage)
        
        if abs_deviation >= 50:
            return SeverityEnum.CRITICAL
        elif abs_deviation >= 25:
            return SeverityEnum.HIGH
        elif abs_deviation >= 10:
            return SeverityEnum.MEDIUM
        else:
            return SeverityEnum.LOW
    
    def calculate_deviation_percentage(self) -> Optional[float]:
        """Calculate percentage deviation from normal range midpoint.
        
        Returns:
            Percentage deviation (positive = above normal, negative = below normal)
        """
        if self.normal_range_low is None or self.normal_range_high is None:
            return None
        
        midpoint = (self.normal_range_low + self.normal_range_high) / 2
        range_width = self.normal_range_high - self.normal_range_low
        
        if range_width == 0:
            return None
        
        deviation = ((self.value - midpoint) / range_width) * 100
        return round(deviation, 1)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "test_name": "Fasting Blood Sugar",
                "value": 145.0,
                "unit": "mg/dL",
                "normal_range": "70-99",
                "normal_range_low": 70.0,
                "normal_range_high": 99.0,
                "is_abnormal": True,
                "severity": "HIGH",
                "deviation_percentage": 61.5,
                "interpretation": "Elevated fasting glucose indicating possible diabetes",
                "risk_indicators": ["Diabetes", "Metabolic syndrome"]
            }
        }
    }


class ClinicalAbnormalitySchema(BaseModel):
    """Schema for clinical findings abnormality.
    
    Similar to lab abnormality but for non-lab clinical findings.
    """
    
    finding_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of clinical finding"
    )
    
    finding_type: str = Field(
        ...,
        description="Type of finding (e.g., 'symptom', 'vital', 'examination')"
    )
    
    description: str = Field(
        ...,
        max_length=1000,
        description="Detailed description of finding"
    )
    
    is_abnormal: bool = Field(
        default=False,
        description="Whether finding is abnormal"
    )
    
    severity: SeverityEnum = Field(
        default=SeverityEnum.LOW,
        description="Clinical severity"
    )
    
    associated_conditions: list[str] = Field(
        default_factory=list,
        description="Associated medical conditions"
    )
    
    requires_immediate_action: bool = Field(
        default=False,
        description="Whether finding requires immediate physician action"
    )
    
    @field_validator("finding_name", "description")
    @classmethod
    def validate_fields(cls, v: str) -> str:
        """Ensure fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
