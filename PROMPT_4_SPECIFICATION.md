# PROMPT 4 SPECIFICATION: Service Layer Implementation

## Complete Specification for Service Layer Development

This document specifies exactly what needs to be built in Prompt 4 to complete Modules A-D.

---

## PROMPT 4: Build Service Layer with Business Logic

### Overview
Create 5 service classes that implement all business logic, using repositories for data access.

Services handle:
- Workflow orchestration
- State machine enforcement
- LLM integration
- Validation rules
- Audit logging
- External integrations

---

## SERVICE 1: ConversationService

### Location
`backend/app/services/conversation.py`

### Class
```python
class ConversationService:
    def __init__(self, db: Session):
        self.session_repo = SessionRepository(db)
        self.turn_repo = ConversationTurnRepository(db)
        self.entity_repo = ExtractedEntityRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.ai_provider = AIProvider()  # Mock/Ollama/OpenAI
```

### Methods to Implement

#### 1. `start_conversation(patient_id: UUID, mode: str) -> Session`
- Create new session via session_repo
- Set current_section = "CHIEF_COMPLAINT"
- Log "SESSION_STARTED" to audit
- Return session

**Usage:**
```python
session = service.start_conversation(patient_id, mode="MODERN")
```

#### 2. `get_section_question(session_id: UUID) -> str`
- Get current section from session
- Generate question based on section
- For CHIEF_COMPLAINT: "What brings you in today?"
- For HPI: "How long have you had this?"
- For SOCRATES: Generate sub-question (SITE→CHARACTER→AGGRAVATING→...)
- For PMH: "Do you have any past medical conditions?"
- Return question string

**Usage:**
```python
question = service.get_section_question(session_id)
# Output: "What is the character of your pain?"
```

#### 3. `add_turn(session_id: UUID, user_input: str) -> dict`
**Core method - implements Module A conversation logic**

Steps:
1. Get session and validate (not completed)
2. Get next turn_index
3. Create PATIENT turn via turn_repo
4. Extract entities from user_input via LLM:
   - Call ai_provider.extract_information(user_input)
   - Validate output with ExtractedEntity schema
   - Save each entity via entity_repo.create_entity()
5. Check for red flags (deterministic, hardcoded):
   ```python
   RED_FLAGS = {
       "chest pain": HIGH,
       "difficulty breathing": HIGH,
       "loss of consciousness": CRITICAL,
       "severe headache": MEDIUM,
       ...
   }
   ```
6. If red flag detected: update session safety_status = "WARNING" or "ESCALATED"
7. Generate AI response based on section:
   - Use ai_provider.generate_response(user_input, context)
   - Context = current section + conversation history
8. Create SYSTEM turn via turn_repo
9. Save extracted_data from both turns
10. Log to audit: "TURN_ADDED"
11. Check if section complete → auto-advance or ask for next section
12. Return dict with:
    - ai_response: str
    - next_section: str
    - section_complete: bool
    - safety_alerts: dict
    - turn_id: UUID

**Usage:**
```python
result = service.add_turn(
    session_id,
    "I've had a sharp chest pain since yesterday"
)
# Result:
# {
#   "ai_response": "That sounds serious. Have you had similar pain before?",
#   "next_section": "HPI",
#   "section_complete": False,
#   "safety_alerts": {"chest_pain": "HIGH"},
#   "turn_id": "..."
# }
```

#### 4. `advance_section(session_id: UUID, next_section: str) -> Session`
- Validate section progression (enforce order):
  ```
  CHIEF_COMPLAINT → HPI → SOCRATES → PMH → PSH → 
  DRUG_HISTORY → ALLERGY_HISTORY → FAMILY_HISTORY → 
  PERSONAL_HISTORY → ROS → COMPLETED
  ```
- Reject if trying to skip or go backward
- Update session via session_repo.update_section()
- Reset socrates_state if leaving SOCRATES
- Log to audit: "SECTION_ADVANCED"
- Return updated session

**Usage:**
```python
session = service.advance_section(session_id, "SOCRATES")
# Raises ValueError if HPI not completed
```

#### 5. `get_conversation_history(session_id: UUID) -> dict`
- Fetch all turns via turn_repo.get_turns_by_session()
- Fetch extracted entities via entity_repo.get_entities_by_session()
- Fetch current session
- Return dict:
  ```python
  {
      "session_id": UUID,
      "current_section": str,
      "turn_count": int,
      "turns": [
          {
              "turn_index": int,
              "speaker": "PATIENT" | "SYSTEM",
              "content": str,
              "section": str,
              "extracted_data": dict,
              "timestamp": datetime
          }
      ],
      "entities": [
          {
              "entity_type": str,
              "entity_name": str,
              "value": str,
              "confidence": float
          }
      ],
      "safety_status": str,
      "safety_alerts": dict
  }
  ```

#### 6. `complete_conversation(session_id: UUID) -> Session`
- Validate all sections completed
- Update session via session_repo.complete_session()
- Update session.structured_history with all extracted entities
- Log to audit: "CONVERSATION_COMPLETED"
- Return session

#### 7. `get_socrates_state(session_id: UUID) -> str`
- Get current SOCRATES sub-state
- States: SITE → CHARACTER → AGGRAVATING → RELIEVING → TIMING → SEVERITY
- Return current state or None if not in SOCRATES section

#### 8. `acknowledge_disclaimer(session_id: UUID) -> Session`
- Call session_repo.acknowledge_disclaimer()
- Log to audit: "DISCLAIMER_ACKNOWLEDGED"
- Return session

#### 9. `handle_safety_escalation(session_id: UUID, reason: str) -> Session`
- Update safety_status = "ESCALATED"
- Log alert to audit: "SAFETY_ESCALATED"
- Notify physician (log to audit for now)
- Return session

### Error Handling
- Raise `ValueError` if section progression invalid
- Raise `ValueError` if conversation already completed
- Raise `ValidationError` if extracted data invalid
- Raise `AIProviderError` if LLM call fails (graceful fallback)
- Log all errors to audit

### Tests Required
```
✓ test_start_conversation()
✓ test_get_section_question() for each section
✓ test_add_turn() with entity extraction
✓ test_add_turn() with red flag detection
✓ test_advance_section() valid progression
✓ test_advance_section() invalid progression (raises)
✓ test_complete_conversation()
✓ test_socrates_state_machine()
✓ test_safety_escalation()
✓ test_ayush_mode_branching()
```

---

## SERVICE 2: DocumentService

### Location
`backend/app/services/document.py`

### Class
```python
class DocumentService:
    def __init__(self, db: Session):
        self.doc_repo = DocumentRepository(db)
        self.entity_repo = ExtractedEntityRepository(db)
        self.session_repo = SessionRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.ai_provider = AIProvider()
```

### Methods to Implement

#### 1. `upload_document(session_id: UUID, file: UploadFile) -> Document`
**Module B: Step 1 - UPLOAD & VALIDATE**

Steps:
1. Validate file:
   - Check mime_type (application/pdf, image/png, image/jpeg)
   - Check file_size ≤ 25MB
   - Read file into bytes
2. Create document record via doc_repo.create_document()
3. Save file to disk or cloud storage
4. Log to audit: "DOCUMENT_UPLOADED"
5. Return Document

**Usage:**
```python
document = service.upload_document(session_id, file)
```

#### 2. `extract_text(document_id: UUID) -> str`
**Module B: Step 2 - EXTRACT (OCR/pypdf)**

Steps:
1. Get document via doc_repo.get_document()
2. Read file from storage
3. Extract text:
   - If PDF: use pypdf
     ```python
     import pypdf
     reader = pypdf.PdfReader(file_path)
     text = "".join(page.extract_text() for page in reader.pages)
     ```
   - If PNG/JPEG: use pytesseract
     ```python
     from PIL import Image
     import pytesseract
     img = Image.open(file_path)
     text = pytesseract.image_to_string(img)
     ```
4. Update document.raw_text via doc_repo.update_upload_status()
5. Update status = "EXTRACTED"
6. Log to audit: "DOCUMENT_EXTRACTED"
7. Return extracted text

#### 3. `extract_entities(document_id: UUID) -> List[ExtractedEntity]`
**Module B: Step 3 - STRUCTURE (LLM extraction)**

Steps:
1. Get document and raw_text
2. Call LLM:
   ```python
   prompt = f"""
   Extract medical entities from text:
   {raw_text}
   
   Return JSON array:
   [
       {{"type": "LAB_RESULT", "name": "...", "value": "...", "unit": "...", "range": "..."}},
       {{"type": "MEDICATION", "name": "...", "dosage": "..."}},
       {{"type": "DIAGNOSIS", "name": "..."}},
       ...
   ]
   """
   response = ai_provider.extract_information(raw_text, schema=ExtractedEntitySchema)
   ```
3. Validate each entity with ExtractedEntitySchema (Pydantic)
4. Save entities via entity_repo.create_entity():
   - For LAB_RESULT: run lab_abnormality_detection()
   - Set is_abnormal based on result
5. Log to audit: "ENTITIES_EXTRACTED"
6. Return list of entities

#### 4. `validate_lab_results(document_id: UUID) -> dict`
**Module B: Step 4 - VALIDATE (Deterministic)**

Steps:
1. Get all LAB_RESULT entities for document
2. For each lab result:
   - Extract numeric_value, unit, reference_range
   - Call detect_lab_abnormality() (from schemas)
   - Update entity.is_abnormal based on result
   - Save via entity_repo.update_abnormality()
3. Collect abnormal results
4. Log to audit: "LAB_VALIDATION_COMPLETE"
5. Return dict:
   ```python
   {
       "total_labs": int,
       "abnormal_count": int,
       "abnormal_results": [
           {
               "test_name": str,
               "value": float,
               "normal_range": str,
               "severity": "LOW" | "MEDIUM" | "HIGH"
           }
       ]
   }
   ```

#### 5. `normalize_chronological_data(document_id: UUID) -> None`
**Module B: Step 5 - CHRONOLOGICAL NORMALIZATION**

Steps:
1. Get all extracted entities
2. For each entity with date information:
   - Parse date strings to ISO format YYYY-MM-DD
   - Update metadata_json with normalized date
3. For each numeric value:
   - Normalize units (e.g., mg → µg conversion)
   - Store original and normalized in metadata_json
4. Save entities via entity_repo.update_entity()
5. Log to audit: "CHRONOLOGICAL_NORMALIZED"

#### 6. `get_document_summary(document_id: UUID) -> dict`
- Fetch document
- Fetch extracted entities
- Return summary:
  ```python
  {
      "filename": str,
      "upload_date": datetime,
      "extraction_status": str,
      "entity_count": int,
      "abnormal_lab_count": int,
      "entities_by_type": {
          "LAB_RESULT": [...],
          "MEDICATION": [...],
          ...
      }
  }
  ```

#### 7. `process_document_end_to_end(session_id: UUID, file: UploadFile) -> dict`
**Convenience method - orchestrates full pipeline**

Steps:
1. Upload document
2. Extract text
3. Extract entities
4. Validate labs
5. Normalize dates
6. Return summary

**Usage:**
```python
result = service.process_document_end_to_end(session_id, file)
# Fully processed document ready for summary generation
```

### Dependencies
```
pip install pypdf pillow pytesseract
```

### Error Handling
- Raise `ValueError` if file type invalid
- Raise `ValueError` if file > 25MB
- Raise `OCRError` if OCR fails (fallback to raw text)
- Raise `ValidationError` if extracted entities invalid
- Raise `AIProviderError` if LLM fails
- Log all errors to audit

### Tests Required
```
✓ test_upload_document() valid file
✓ test_upload_document() invalid type (raises)
✓ test_upload_document() oversized (raises)
✓ test_extract_text() PDF
✓ test_extract_text() PNG
✓ test_extract_entities() entity extraction
✓ test_validate_lab_results() abnormality detection
✓ test_normalize_chronological_data()
✓ test_process_document_end_to_end()
```

---

## SERVICE 3: SummaryService

### Location
`backend/app/services/summary.py`

### Class
```python
class SummaryService:
    def __init__(self, db: Session):
        self.summary_repo = SummaryRepository(db)
        self.session_repo = SessionRepository(db)
        self.entity_repo = ExtractedEntityRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.ai_provider = AIProvider()
```

### Methods to Implement

#### 1. `generate_summary(session_id: UUID) -> Summary`
**Module C: Generate Summary from A + B**

Steps:
1. Get session + structured_history (Module A data)
2. Get all extracted entities (Module B data)
3. Build context:
   ```python
   context = {
       "conversation": session.structured_history,
       "documents": {
           "lab_results": entity_repo.get_lab_results(session_id),
           "medications": entity_repo.get_medications(session_id),
           "symptoms": entity_repo.get_symptoms(session_id),
           "abnormal_labs": entity_repo.get_abnormal_entities(session_id)
       }
   }
   ```
4. Create summary record (status = "GENERATING")
5. Call LLM:
   ```python
   prompt = f"""
   Generate strict clinical summary from:
   
   Conversation:
   {json.dumps(context['conversation'], indent=2)}
   
   Documents:
   {json.dumps(context['documents'], indent=2)}
   
   Return JSON with fields:
   {{
       "chief_complaint": "...",
       "hpi": "...",
       "pmh": "...",
       ...
       "key_findings": [...],
       "red_flags": [...],
       "recommendations": [...],
       "uncertainty_notes": "..."
   }}
   """
   output = ai_provider.generate_response(prompt, schema=ClinicalSummaryContent)
   ```
6. Validate output against ClinicalSummaryContent (Pydantic)
7. Update summary.structured_summary
8. Update status = "GENERATED"
9. Log to audit: "SUMMARY_GENERATED"
10. Return summary

#### 2. `validate_summary_structure(summary_id: UUID) -> bool`
- Validate summary_content against ClinicalSummaryContent schema
- Check all required fields present
- Check no null/empty values
- Return True or raise ValidationError

#### 3. `send_for_physician_review(summary_id: UUID) -> Summary`
- Update workflow_status = "PHYSICIAN_REVIEW"
- Log to audit: "SUMMARY_SENT_FOR_REVIEW"
- Return summary (for physician UI)

#### 4. `physician_accept(summary_id: UUID, physician_id: str) -> Summary`
- Call summary_repo.accept_summary(summary_id, physician_id)
- Log to audit: "SUMMARY_ACCEPTED"
- Return summary

#### 5. `physician_reject(summary_id: UUID, rejection_reason: str) -> Summary`
- Call summary_repo.reject_summary(summary_id, rejection_reason)
- Log to audit: "SUMMARY_REJECTED"
- Return summary

#### 6. `physician_edit(summary_id: UUID, edited_content: ClinicalSummaryContent) -> Summary`
- Validate edited_content (Pydantic)
- Call summary_repo.set_physician_edited()
- Increment summary.version
- Log to audit: "SUMMARY_EDITED_BY_PHYSICIAN"
- Return summary

#### 7. `regenerate_summary(session_id: UUID) -> Summary`
- Get latest summary for session
- Increment version
- Call generate_summary() again
- Return new summary

#### 8. `get_summary_with_audit(summary_id: UUID) -> dict`
- Get summary
- Get audit logs for summary (created, reviewed, accepted)
- Return dict:
  ```python
  {
      "summary": Summary,
      "version": int,
      "status": str,
      "created_at": datetime,
      "ai_generated": ClinicalSummaryContent,
      "physician_edited": ClinicalSummaryContent,  # if edited
      "accepted_by": str,  # if accepted
      "audit_trail": [...]
  }
  ```

### Error Handling
- Raise `ValidationError` if generated summary invalid
- Raise `AIProviderError` if LLM fails
- Raise `ValueError` if summary already accepted
- Log all errors to audit

### Tests Required
```
✓ test_generate_summary() from conversation + docs
✓ test_validate_summary_structure()
✓ test_send_for_physician_review()
✓ test_physician_accept()
✓ test_physician_reject()
✓ test_physician_edit()
✓ test_regenerate_summary()
✓ test_summary_audit_trail()
```

---

## SERVICE 4: ConsentService

### Location
`backend/app/services/consent.py`

### Class
```python
class ConsentService:
    def __init__(self, db: Session):
        self.consent_repo = ConsentRepository(db)
        self.audit_repo = AuditLogRepository(db)
```

### Methods to Implement

#### 1. `grant_consent(session_id: UUID, patient_id: UUID, purpose: str, ip_address: str) -> Consent`
- Call consent_repo.grant_consent()
- Log to audit: "CONSENT_GRANTED"
- Return consent

#### 2. `revoke_consent(patient_id: UUID, purpose: str) -> Consent`
- Get active consent for purpose
- Call consent_repo.revoke_consent()
- Log to audit: "CONSENT_REVOKED"
- Return consent

#### 3. `check_consent(patient_id: UUID, purpose: str) -> bool`
- Call consent_repo.has_active_consent()
- Return True/False

#### 4. `get_consent_history(patient_id: UUID) -> dict`
- Call consent_repo.get_consent_audit_trail()
- Return audit trail

### Tests Required
```
✓ test_grant_consent()
✓ test_revoke_consent()
✓ test_check_consent()
✓ test_get_consent_history()
```

---

## SERVICE 5: IntegrationService

### Location
`backend/app/services/integration.py`

### Class
```python
class IntegrationService:
    def __init__(self, db: Session):
        self.consent_repo = ConsentRepository(db)
        self.fhir_adapter = FHIRAdapter()
        self.abdm_adapter = ABDMAdapter()
        self.audit_repo = AuditLogRepository(db)
```

### Adapters

#### FHIR Adapter
File: `backend/app/integrations/fhir_adapter.py`

```python
class FHIRAdapter:
    def summary_to_fhir_diagnostic_report(
        self, 
        summary: Summary, 
        patient: Patient
    ) -> dict:
        """Convert ClinicalSummary → FHIR DiagnosticReport"""
        # Return FHIR JSON-LD format
        return {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "code": {...},
            "subject": {"reference": f"Patient/{patient.id}"},
            "issued": datetime.now(),
            "result": [...]  # Observations from summary
        }
    
    def entities_to_fhir_observations(
        self, 
        entities: List[ExtractedEntity]
    ) -> List[dict]:
        """Convert ExtractedEntities → FHIR Observations"""
        # Return list of FHIR Observation resources
        return [
            {
                "resourceType": "Observation",
                "code": {...},
                "value": entity.numeric_value or entity.value,
                "referenceRange": entity.reference_range,
                "status": "final"
            }
            for entity in entities
        ]
```

#### ABDM Adapter (Mock)
File: `backend/app/integrations/abdm_adapter.py`

```python
class ABDMAdapter:
    def prepare_for_abdm(
        self,
        session_id: UUID,
        summary: Summary,
        entities: List[ExtractedEntity]
    ) -> dict:
        """Format data for ABDM health record sharing"""
        # Mock: return formatted health record
        return {
            "health_record_id": str(session_id),
            "created_at": datetime.now(),
            "clinical_summary": summary.structured_summary,
            "lab_results": [e for e in entities if e.entity_type == "LAB_RESULT"],
            "medications": [e for e in entities if e.entity_type == "MEDICATION"]
        }
    
    def share_to_abdm(
        self,
        patient_id: UUID,
        health_record: dict
    ) -> dict:
        """Mock ABDM API call"""
        # Return mock response
        return {
            "status": "success",
            "abdm_reference_id": str(uuid.uuid4()),
            "timestamp": datetime.now()
        }
```

### Methods to Implement

#### 1. `export_to_fhir(session_id: UUID) -> dict`
**Check consent before export**

Steps:
1. Get session, summary, entities
2. Check consent: `consent_repo.has_active_consent(patient_id, "fhir_export")`
3. If no consent: raise PermissionError
4. Convert to FHIR via adapter
5. Log to audit: "FHIR_EXPORTED"
6. Return FHIR JSON

#### 2. `share_to_abdm(session_id: UUID) -> dict`
**Mock ABDM sharing**

Steps:
1. Get session, summary, entities, patient
2. Check consent: `consent_repo.has_active_consent(patient_id, "abdm_integration")`
3. If no consent: raise PermissionError
4. Prepare data via ABDM adapter
5. Call mock ABDM API
6. Log to audit: "SHARED_TO_ABDM"
7. Return response

#### 3. `export_summary(session_id: UUID, format: str) -> dict | str`
- Formats: "json", "fhir", "pdf"
- Check consent for export
- Return formatted data

### Error Handling
- Raise `PermissionError` if no consent
- Raise `IntegrationError` if export fails
- Log all errors to audit

### Tests Required
```
✓ test_export_to_fhir() with consent
✓ test_export_to_fhir() without consent (raises)
✓ test_share_to_abdm() with consent
✓ test_share_to_abdm() without consent (raises)
✓ test_fhir_adapter() summary conversion
✓ test_fhir_adapter() entity conversion
✓ test_abdm_adapter() mock sharing
```

---

## SERVICE INITIALIZATION

File: `backend/app/services/__init__.py`

```python
from app.services.conversation import ConversationService
from app.services.document import DocumentService
from app.services.summary import SummaryService
from app.services.consent import ConsentService
from app.services.integration import IntegrationService

__all__ = [
    "ConversationService",
    "DocumentService",
    "SummaryService",
    "ConsentService",
    "IntegrationService"
]
```

---

## EXPECTED COMPLETION

After Prompt 4, the application will have:

### ✓ Module A: Conversation
- State machine enforcement
- Adaptive questioning
- SOCRATES sub-state machine
- Red-flag detection
- AYUSH mode support

### ✓ Module B: Document
- Upload with validation
- OCR text extraction
- LLM entity extraction
- Lab validation
- Chronological normalization

### ✓ Module C: Summary
- Conversation + document synthesis
- LLM summary generation
- Physician review workflow
- Version tracking

### ✓ Module D: Consent/Integration
- Consent audit trail
- FHIR export adapter
- ABDM mock adapter
- Adapter isolation pattern

### ✓ Full Stack
- ORM ✓ (Prompt 1)
- Database ✓ (Prompt 2)
- Repositories ✓ (Prompt 3)
- Services 🔄 (Prompt 4)
- API Routes (Prompt 5)
- Frontend (Prompt 6)

---

## NEXT PROMPTS AFTER SERVICE LAYER

**Prompt 5:** Create API Routes
- Conversation endpoints
- Document endpoints
- Summary endpoints
- Consent endpoints
- Integration endpoints

**Prompt 6:** Create Frontend
- Conversation UI
- Document upload UI
- Summary review UI
- Consent UI
- Physician dashboard

---

## DELIVERABLES FOR PROMPT 4

- [ ] 5 service classes (147 methods total)
- [ ] 2 integration adapters (FHIR, ABDM)
- [ ] AI provider abstraction usage
- [ ] Complete error handling
- [ ] Comprehensive audit logging
- [ ] All tests passing (50+ tests)
- [ ] Documentation
- [ ] Ready for API routes (Prompt 5)
