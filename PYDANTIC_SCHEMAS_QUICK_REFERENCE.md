# PYDANTIC SCHEMAS QUICK REFERENCE

## Schemas Overview

| Schema | Purpose | File | Fields |
|--------|---------|------|--------|
| ConversationResponseSchema | AI conversation responses | conversation.py | response, confidence, next_section |
| DocumentExtractionSchema | Document extraction output | document.py | extracted_text, tables, entities, confidence |
| LabAbnormalitySchema | Lab value abnormality | lab.py | test_name, value, normal_range, severity |
| ClinicalSummarySchema | Full clinical summary | summary.py | All clinical findings + red_flags |
| RedFlagDetector | Deterministic red flag detection | red_flags.py | Hardcoded rules (no LLM) |

---

## Quick Examples

### Conversation Response
```python
from app.ai.schemas import ConversationResponseSchema

response = ConversationResponseSchema(
    response="Tell me about your symptoms",
    confidence=0.95,
    next_section="HPI"
)
```

### Document Extraction
```python
from app.ai.schemas import (
    DocumentExtractionSchema,
    ExtractedEntity,
    EntityTypeEnum,
    DocumentTypeEnum
)

entity = ExtractedEntity(
    entity_type=EntityTypeEnum.LAB_RESULT,
    entity_name="Glucose",
    value="145 mg/dL",
    numeric_value=145.0,
    is_abnormal=True,
    confidence_score=0.95
)

doc = DocumentExtractionSchema(
    document_type=DocumentTypeEnum.LAB_REPORT,
    entities=[entity]
)

# Use filters
abnormal = doc.abnormal_entities
labs = doc.lab_results
meds = doc.medications
```

### Lab Abnormality Detection
```python
from app.ai.schemas import LabAbnormalitySchema, SeverityEnum

lab = LabAbnormalitySchema(
    test_name="Glucose",
    value=245.0,
    normal_range="70-99",
    normal_range_low=70.0,
    normal_range_high=99.0,
    is_abnormal=True,
    severity=SeverityEnum.HIGH
)

# Methods
is_abnormal = lab.calculate_abnormality()  # True
severity = lab.calculate_severity()  # HIGH
deviation = lab.calculate_deviation_percentage()  # 147%
```

### Red Flag Detection (Deterministic)
```python
from app.ai.schemas import RedFlagDetector

# Single symptom
flag = RedFlagDetector.detect_symptom_red_flags("chest pain")
# Returns: RedFlag with CRITICAL severity

# Vital signs
flag = RedFlagDetector.detect_vital_sign_red_flags("oxygen_saturation", 85)
# Returns: RedFlag with CRITICAL severity

# Lab values
flag = RedFlagDetector.detect_lab_red_flags("troponin", 0.08)
# Returns: RedFlag with CRITICAL severity

# Combined
flags = RedFlagDetector.detect_combination_red_flags(
    symptoms=["chest pain"],
    vitals={"systolic_bp": 185},
    labs={"troponin": 0.05}
)
```

### Clinical Summary
```python
from app.ai.schemas import (
    ClinicalSummarySchema,
    ClinicalItem,
    InformationStatus,
    MedicationItem
)

summary = ClinicalSummarySchema(
    session_id="abc-123",
    chief_complaint=[
        ClinicalItem(
            name="Chest pain",
            status=InformationStatus.KNOWN,
            details="Retrosternal, 7/10"
        )
    ],
    medications=[
        MedicationItem(
            name="Aspirin",
            dosage="100mg",
            frequency="daily",
            route="oral"
        )
    ],
    generated_summary_text="Patient with acute chest pain..."
)
```

---

## Validation Examples

### Valid Conversation Response
```python
response = ConversationResponseSchema(
    response="Can you describe the pain?",
    confidence=0.95,
    next_section="HPI"
)
# ✓ Valid
```

### Invalid Conversation Response
```python
# ✗ Empty response
ConversationResponseSchema(response="", confidence=0.95, next_section="HPI")

# ✗ Invalid section
ConversationResponseSchema(
    response="Test",
    confidence=0.95,
    next_section="INVALID"
)

# ✗ Confidence out of range
ConversationResponseSchema(
    response="Test",
    confidence=1.5,
    next_section="HPI"
)
```

---

## Red Flag Severity Levels

| Level | Threshold | Action |
|-------|-----------|--------|
| CRITICAL | ≥50% deviation | Immediate escalation |
| HIGH | ≥25% deviation | Urgent review |
| MEDIUM | ≥10% deviation | Routine review |
| LOW | <10% deviation | Monitor |

---

## Red Flag Categories

- CARDIOVASCULAR — Heart, blood vessels
- RESPIRATORY — Lungs, breathing
- NEUROLOGICAL — Brain, nerves
- METABOLIC — Glucose, electrolytes
- INFECTIOUS — Fever, infection
- HEMORRHAGE — Bleeding
- TOXIC — Poisoning, overdose
- ALLERGIC — Allergic reactions
- PSYCHIATRIC — Mental health
- UNKNOWN — Other

---

## Hardcoded Red Flag Rules

### Critical Symptoms (Immediate Escalation)
- Chest pain / Acute chest pain
- Sudden severe headache
- Loss of consciousness
- Inability to speak
- Facial drooping
- Severe allergic reaction
- Anaphylaxis
- Uncontrolled bleeding
- Severe stroke symptoms

### Critical Vital Signs (Immediate Escalation)
- Systolic BP ≥180 mmHg
- Oxygen saturation ≤90%
- Heart rate ≤50 or ≥120
- Respiratory rate ≥30

### Critical Lab Values (Immediate Escalation)
- Troponin ≥0.04 ng/mL
- Glucose ≤50 mg/dL
- Hemoglobin ≤7 g/dL
- Potassium ≥6.0 mEq/L
- INR ≥4.0

---

## Field Validators

### ConversationResponseSchema
```python
response:       # 1-5000 chars, non-empty
confidence:     # 0.0-1.0, rounded to 0.001
next_section:   # Valid section from enum
```

### DocumentExtractionSchema
```python
confidence:     # 0.0-1.0
tables:         # Must have headers or rows
entities:       # All must be valid
```

### LabAbnormalitySchema
```python
test_name:      # 1-200 chars, non-empty
value:          # Numeric
normal_range:   # Non-empty string
severity:       # Only HIGH+ if is_abnormal=True
```

---

## Entity Types

- LAB_RESULT
- VITAL_SIGN
- MEDICATION
- DIAGNOSIS
- PROCEDURE
- ALLERGY
- IMAGING_FINDING
- OTHER

---

## Document Types

- LAB_REPORT
- IMAGING_REPORT
- PRESCRIPTION
- DISCHARGE_SUMMARY
- CLINICAL_NOTE
- UNKNOWN

---

## Testing

### Run All Tests
```bash
python -m pytest test_ai_schemas.py -v
```

### Test Coverage
- 27+ test methods
- All schemas tested
- All validators tested
- Red flag detection tested
- Integration tests

---

## Integration

### Service Usage
```python
from app.modules.documents.service import DocumentService

# Service automatically uses schemas
service = DocumentService()
doc = await service.upload_and_process_document(...)
# Returns: DocumentExtractionSchema validated output
```

### Provider Usage
```python
from app.ai.providers import get_llm_provider

provider = get_llm_provider()
result = provider.generate_structured(
    prompt="...",
    schema_class=DocumentExtractionSchema  # Auto-validates
)
# Returns: Validated schema instance
```

---

## Files

```
backend/app/ai/schemas/
├── __init__.py — Exports
├── conversation.py — ConversationResponseSchema
├── document.py — DocumentExtractionSchema
├── lab.py — LabAbnormalitySchema
├── red_flags.py — RedFlagDetector (deterministic)
└── summary.py — ClinicalSummarySchema

backend/test_ai_schemas.py — 350+ lines of tests
```

---

## Key Points

✓ **Deterministic Red Flags** — Hardcoded rules, not LLM
✓ **Type Safe** — 100% type hints
✓ **Validated** — Field-level validators
✓ **Tested** — 27+ test methods
✓ **Documented** — Comprehensive docstrings
✓ **Production-Ready** — Error handling robust

---

## Status

**Implementation:** ✓ COMPLETE  
**Testing:** ✓ COMPREHENSIVE  
**Documentation:** ✓ EXTENSIVE  
**Production-Ready:** ✓ YES
