"""Comprehensive tests for AI schemas and red flag detection."""

import pytest
from pydantic import ValidationError

from app.ai.schemas import (
    ConversationResponseSchema,
    DocumentExtractionSchema,
    LabAbnormalitySchema,
    SeverityEnum,
    RedFlagDetector,
    RedFlagSeverity,
    RedFlagCategory,
    ExtractedEntity,
    EntityTypeEnum,
    DocumentTypeEnum,
)


class TestConversationResponseSchema:
    """Tests for conversation response schema."""
    
    def test_valid_response(self):
        """Test creating valid conversation response."""
        response = ConversationResponseSchema(
            response="Tell me about your symptoms",
            confidence=0.95,
            next_section="HPI"
        )
        assert response.response == "Tell me about your symptoms"
        assert response.confidence == 0.95
        assert response.next_section == "HPI"
    
    def test_confidence_validation(self):
        """Test confidence must be 0-1."""
        with pytest.raises(ValidationError):
            ConversationResponseSchema(
                response="Test",
                confidence=1.5,  # Invalid
                next_section="HPI"
            )
    
    def test_empty_response_validation(self):
        """Test response cannot be empty."""
        with pytest.raises(ValidationError):
            ConversationResponseSchema(
                response="",
                confidence=0.95,
                next_section="HPI"
            )
    
    def test_invalid_section(self):
        """Test invalid section is rejected."""
        with pytest.raises(ValidationError):
            ConversationResponseSchema(
                response="Test",
                confidence=0.95,
                next_section="INVALID_SECTION"
            )
    
    def test_confidence_rounding(self):
        """Test confidence is rounded to 3 decimals."""
        response = ConversationResponseSchema(
            response="Test",
            confidence=0.123456789,
            next_section="HPI"
        )
        assert response.confidence == 0.123


class TestDocumentExtractionSchema:
    """Tests for document extraction schema."""
    
    def test_valid_document_extraction(self):
        """Test creating valid document extraction."""
        entity = ExtractedEntity(
            entity_type=EntityTypeEnum.LAB_RESULT,
            entity_name="Hemoglobin",
            value="14.5 g/dL",
            numeric_value=14.5,
            unit="g/dL",
            confidence_score=0.95
        )
        
        doc = DocumentExtractionSchema(
            document_type=DocumentTypeEnum.LAB_REPORT,
            extracted_text="Lab report text",
            entities=[entity],
            confidence=0.90
        )
        
        assert doc.document_type == DocumentTypeEnum.LAB_REPORT
        assert len(doc.entities) == 1
        assert doc.confidence == 0.90
    
    def test_abnormal_entities_filter(self):
        """Test abnormal_entities property filters correctly."""
        entities = [
            ExtractedEntity(
                entity_type=EntityTypeEnum.LAB_RESULT,
                entity_name="Test1",
                value="123",
                is_abnormal=True,
                confidence_score=0.95
            ),
            ExtractedEntity(
                entity_type=EntityTypeEnum.LAB_RESULT,
                entity_name="Test2",
                value="456",
                is_abnormal=False,
                confidence_score=0.95
            ),
        ]
        
        doc = DocumentExtractionSchema(entities=entities)
        assert len(doc.abnormal_entities) == 1
        assert doc.abnormal_entities[0].entity_name == "Test1"
    
    def test_lab_results_filter(self):
        """Test lab_results property filters correctly."""
        entities = [
            ExtractedEntity(
                entity_type=EntityTypeEnum.LAB_RESULT,
                entity_name="Glucose",
                value="145",
                confidence_score=0.95
            ),
            ExtractedEntity(
                entity_type=EntityTypeEnum.MEDICATION,
                entity_name="Metformin",
                value="500mg",
                confidence_score=0.95
            ),
        ]
        
        doc = DocumentExtractionSchema(entities=entities)
        assert len(doc.lab_results) == 1
        assert doc.lab_results[0].entity_name == "Glucose"
    
    def test_medications_filter(self):
        """Test medications property filters correctly."""
        entities = [
            ExtractedEntity(
                entity_type=EntityTypeEnum.MEDICATION,
                entity_name="Aspirin",
                value="100mg",
                confidence_score=0.95
            ),
            ExtractedEntity(
                entity_type=EntityTypeEnum.LAB_RESULT,
                entity_name="Glucose",
                value="145",
                confidence_score=0.95
            ),
        ]
        
        doc = DocumentExtractionSchema(entities=entities)
        assert len(doc.medications) == 1
        assert doc.medications[0].entity_name == "Aspirin"
    
    def test_confidence_validation(self):
        """Test confidence must be 0-1."""
        with pytest.raises(ValidationError):
            DocumentExtractionSchema(
                confidence=1.5  # Invalid
            )


class TestLabAbnormalitySchema:
    """Tests for lab abnormality schema."""
    
    def test_normal_lab_result(self):
        """Test normal lab result."""
        lab = LabAbnormalitySchema(
            test_name="Hemoglobin",
            value=14.5,
            unit="g/dL",
            normal_range="13.0-17.5",
            normal_range_low=13.0,
            normal_range_high=17.5,
            is_abnormal=False
        )
        assert lab.is_abnormal is False
        assert lab.severity == SeverityEnum.LOW
    
    def test_abnormal_high_lab_result(self):
        """Test abnormal high lab result."""
        lab = LabAbnormalitySchema(
            test_name="Glucose",
            value=250.0,
            unit="mg/dL",
            normal_range="70-99",
            normal_range_low=70.0,
            normal_range_high=99.0,
            is_abnormal=True,
            severity=SeverityEnum.HIGH
        )
        assert lab.is_abnormal is True
        assert lab.severity == SeverityEnum.HIGH
    
    def test_abnormal_low_lab_result(self):
        """Test abnormal low lab result."""
        lab = LabAbnormalitySchema(
            test_name="Hemoglobin",
            value=7.0,
            unit="g/dL",
            normal_range="13.0-17.5",
            normal_range_low=13.0,
            normal_range_high=17.5,
            is_abnormal=True,
            severity=SeverityEnum.CRITICAL
        )
        assert lab.is_abnormal is True
        assert lab.severity == SeverityEnum.CRITICAL
    
    def test_calculate_abnormality_above_range(self):
        """Test abnormality calculation for value above range."""
        lab = LabAbnormalitySchema(
            test_name="Glucose",
            value=150.0,
            unit="mg/dL",
            normal_range="70-99",
            normal_range_low=70.0,
            normal_range_high=99.0
        )
        assert lab.calculate_abnormality() is True
    
    def test_calculate_abnormality_below_range(self):
        """Test abnormality calculation for value below range."""
        lab = LabAbnormalitySchema(
            test_name="Glucose",
            value=50.0,
            unit="mg/dL",
            normal_range="70-99",
            normal_range_low=70.0,
            normal_range_high=99.0
        )
        assert lab.calculate_abnormality() is True
    
    def test_calculate_abnormality_within_range(self):
        """Test abnormality calculation for value within range."""
        lab = LabAbnormalitySchema(
            test_name="Glucose",
            value=85.0,
            unit="mg/dL",
            normal_range="70-99",
            normal_range_low=70.0,
            normal_range_high=99.0
        )
        assert lab.calculate_abnormality() is False
    
    def test_calculate_deviation_percentage(self):
        """Test deviation percentage calculation."""
        lab = LabAbnormalitySchema(
            test_name="Glucose",
            value=250.0,
            unit="mg/dL",
            normal_range="70-99",
            normal_range_low=70.0,
            normal_range_high=99.0
        )
        deviation = lab.calculate_deviation_percentage()
        assert deviation is not None
        assert deviation > 0  # Above normal


class TestRedFlagDetection:
    """Tests for deterministic red flag detection."""
    
    def test_detect_chest_pain(self):
        """Test detection of chest pain red flag."""
        flag = RedFlagDetector.detect_symptom_red_flags("chest pain")
        assert flag is not None
        assert flag.category == RedFlagCategory.CARDIOVASCULAR
        assert flag.severity == RedFlagSeverity.CRITICAL
        assert flag.requires_immediate_escalation is True
    
    def test_detect_shortness_of_breath(self):
        """Test detection of SOB red flag."""
        flag = RedFlagDetector.detect_symptom_red_flags("shortness of breath")
        assert flag is not None
        assert flag.category == RedFlagCategory.RESPIRATORY
        assert flag.severity == RedFlagSeverity.HIGH
    
    def test_detect_sudden_severe_headache(self):
        """Test detection of sudden severe headache."""
        flag = RedFlagDetector.detect_symptom_red_flags("sudden severe headache")
        assert flag is not None
        assert flag.category == RedFlagCategory.NEUROLOGICAL
        assert flag.severity == RedFlagSeverity.CRITICAL
    
    def test_no_red_flag_normal_symptom(self):
        """Test normal symptom doesn't trigger red flag."""
        flag = RedFlagDetector.detect_symptom_red_flags("mild headache")
        assert flag is None
    
    def test_detect_vital_sign_hypertension(self):
        """Test detection of critical hypertension."""
        flag = RedFlagDetector.detect_vital_sign_red_flags("systolic_bp", 185)
        assert flag is not None
        assert flag.category == RedFlagCategory.CARDIOVASCULAR
        assert flag.severity == RedFlagSeverity.HIGH
    
    def test_detect_vital_sign_hypoxia(self):
        """Test detection of critical hypoxia."""
        flag = RedFlagDetector.detect_vital_sign_red_flags("oxygen_saturation", 85)
        assert flag is not None
        assert flag.category == RedFlagCategory.RESPIRATORY
        assert flag.severity == RedFlagSeverity.CRITICAL
    
    def test_detect_lab_troponin(self):
        """Test detection of elevated troponin."""
        flag = RedFlagDetector.detect_lab_red_flags("troponin", 0.05)
        assert flag is not None
        assert flag.category == RedFlagCategory.CARDIOVASCULAR
        assert flag.severity == RedFlagSeverity.CRITICAL
    
    def test_detect_lab_glucose_critical(self):
        """Test detection of critical glucose."""
        flag = RedFlagDetector.detect_lab_red_flags("glucose", 450)
        assert flag is not None
        assert flag.category == RedFlagCategory.METABOLIC
        assert flag.severity == RedFlagSeverity.HIGH
    
    def test_detect_combination_red_flags(self):
        """Test combination red flag detection."""
        symptoms = ["chest pain", "shortness of breath"]
        vitals = {"systolic_bp": 185, "heart_rate": 95}
        
        flags = RedFlagDetector.detect_combination_red_flags(
            symptoms=symptoms,
            vitals=vitals
        )
        
        assert len(flags) > 0
        assert any(f.severity == RedFlagSeverity.CRITICAL for f in flags)
    
    def test_no_false_positives(self):
        """Test that normal findings don't trigger red flags."""
        symptoms = ["mild cough", "slight fatigue"]
        vitals = {"systolic_bp": 120, "heart_rate": 70}
        
        flags = RedFlagDetector.detect_combination_red_flags(
            symptoms=symptoms,
            vitals=vitals
        )
        
        assert len(flags) == 0


class TestSchemaIntegration:
    """Integration tests for all schemas."""
    
    def test_lab_schema_with_abnormality(self):
        """Test lab schema detects and reports abnormality."""
        lab = LabAbnormalitySchema(
            test_name="Potassium",
            value=6.5,
            unit="mEq/L",
            normal_range="3.5-5.0",
            normal_range_low=3.5,
            normal_range_high=5.0,
            is_abnormal=True,
            severity=SeverityEnum.HIGH,
            interpretation="Hyperkalemia detected"
        )
        
        assert lab.calculate_abnormality() is True
        assert lab.severity == SeverityEnum.HIGH
    
    def test_document_with_lab_entities(self):
        """Test document extraction with lab entities."""
        entities = [
            ExtractedEntity(
                entity_type=EntityTypeEnum.LAB_RESULT,
                entity_name="Troponin",
                value="0.05",
                numeric_value=0.05,
                unit="ng/mL",
                is_abnormal=True,
                confidence_score=0.98
            )
        ]
        
        doc = DocumentExtractionSchema(
            document_type=DocumentTypeEnum.LAB_REPORT,
            extracted_text="Cardiac panel results",
            entities=entities
        )
        
        assert len(doc.abnormal_entities) == 1
        assert doc.abnormal_entities[0].entity_name == "Troponin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
