# QUICK REFERENCE: SERVICE LAYER (PROMPT 4)

## Conversation Service

### Import
```python
from app.modules.conversation.service import ClinicalConversationService
from app.modules.conversation.schemas import SessionMode
```

### Usage

**1. Initialize Service**
```python
service = ClinicalConversationService()
db = SessionLocal()
```

**2. Start Conversation**
```python
session = service.create_session(
    patient_id=uuid.uuid4(),
    mode=SessionMode.MODERN,
    disclaimer_acknowledged=True,
    db=db
)
# Returns: SessionModel with current_section="IDENTIFICATION"
```

**3. Get Current State**
```python
state = service.get_session_state(session.id, db)
# Returns: SessionStateResponse with current section, question, history
```

**4. Submit Response & Advance**
```python
result = service.submit_patient_response(
    session_id=session.id,
    raw_text="I have a headache",
    db=db
)
# Returns: ProcessResponseResult with next question and advanced state
```

**5. Resume Conversation**
```python
history = service.get_conversation_history(session.id, db)
# Returns: List[ConversationTurnModel] ordered by turn_index
```

---

## Documents Service

### Import
```python
from app.modules.documents.service import DocumentService
```

### Usage

**1. Initialize Service**
```python
service = DocumentService()
db = SessionLocal()
```

**2. Upload Document**
```python
doc = await service.upload_and_process_document(
    session_id=session.id,
    file=file_upload,  # FastAPI UploadFile
    db=db
)
# Returns: DocumentModel with status="EXTRACTED"
# Automatically extracts entities and applies lab validation
```

**3. List Documents**
```python
docs = service.list_session_documents(session.id, db)
# Returns: List[DocumentModel]
```

**4. Get Extracted Entities**
```python
entities = service.list_session_entities(
    session_id=session.id,
    abnormal_only=True,  # Optional: filter abnormal
    db=db
)
# Returns: List[ExtractedEntityModel]
```

**5. Delete Document**
```python
response = service.delete_document(session.id, doc.id, db)
# Returns: DocumentDeleteResponse
# Removes file from disk and deletes DB records
```

---

## State Machine

### Sections (Linear Order)

```
0. IDENTIFICATION
1. CHIEF_COMPLAINT
2. HPI (with SOCRATES: SITE, ONSET, CHARACTER, RADIATION, 
        ASSOCIATED_SYMPTOMS, TIME_COURSE, EXACERBATING_RELIEVING_FACTORS, SEVERITY)
3. PAST_MEDICAL_HISTORY
4. PAST_SURGICAL_HISTORY
5. MEDICATIONS
6. ALLERGIES
7. FAMILY_HISTORY
8. PERSONAL_HISTORY
9. REVIEW_OF_SYSTEMS
10. COMPLETED
```

### Verification

```python
from app.modules.conversation.state_machine import InterviewStateMachine

sm = InterviewStateMachine()
print(sm.SECTION_ORDER)     # All 11 sections
print(sm.SOCRATES_ORDER)    # All 8 SOCRATES attributes
```

---

## File Validation (Documents)

### Supported MIME Types
```
application/pdf
image/png
image/jpeg
image/jpg
```

### Supported Extensions
```
.pdf
.png
.jpg
.jpeg
```

### Size Limit
```
25MB per file
```

### Validation Errors
```
HTTP 415: Unsupported MIME type or extension
HTTP 413: File too large
```

---

## Lab Abnormality Detection

### Supported Tests
- Hemoglobin
- Glucose (fasting, random, generic)
- Creatinine
- Troponin
- Cholesterol (total, LDL, HDL)
- Triglycerides
- CBC (WBC, Platelets)
- Electrolytes (K, Na)
- Liver enzymes (ALT, AST, SGPT, SGOT)
- Thyroid (TSH)
- Blood urea nitrogen (BUN)
- And 17 more...

### Detection Logic

```python
def evaluate_lab_result(
    test_name: str,
    raw_value: str,
    numeric_value: float,
    unit: str,
    reference_range: Optional[str]
) -> Tuple[bool, Optional[str], Optional[str]]:
    # Returns: (is_abnormal, flag_reason, reference_range_used)
    
    is_abnormal = (numeric_value < low_bound or numeric_value > high_bound)
    return is_abnormal, flag, ref_range
```

---

## Audit Logging

### Logged Events

**Conversation:**
- SESSION_CREATED
- DISCLAIMER_ACKNOWLEDGED
- PATIENT_RESPONSE_RECEIVED
- CLINICAL_EXTRACTION_COMPLETED
- STATE_TRANSITION
- SAFETY_RULE_TRIGGERED
- SESSION_COMPLETED

**Documents:**
- DOCUMENT_UPLOADED
- DOCUMENT_EXTRACTED
- DOCUMENT_EXTRACTION_FAILED
- DOCUMENT_DELETED

### Access Logs
```python
from app.db.models import AuditLog

logs = db.query(AuditLog).filter(
    AuditLog.session_id == session_id
).all()

for log in logs:
    print(f"{log.action} ({log.status}): {log.details}")
```

---

## Error Handling

### Common Exceptions

**Session Not Found**
```python
HTTPException(
    status_code=404,
    detail={"error": "Session not found", "code": "SESSION_NOT_FOUND"}
)
```

**File Too Large**
```python
HTTPException(
    status_code=413,
    detail={"error": "File exceeds 25MB limit", "code": "FILE_TOO_LARGE"}
)
```

**Unsupported File Type**
```python
HTTPException(
    status_code=415,
    detail={"error": "Unsupported format", "code": "UNSUPPORTED_MEDIA_TYPE"}
)
```

**Disclaimer Not Acknowledged**
```python
HTTPException(
    status_code=403,
    detail={"error": "Disclaimer not acknowledged", "code": "DISCLAIMER_NOT_ACKNOWLEDGED"}
)
```

---

## Testing

### Run Tests
```bash
cd backend
python test_service_layer.py
```

### Expected Output
```
======================================================================
TESTING SERVICE LAYER IMPLEMENTATION
======================================================================

[1] Testing ConversationService...
    ✓ start_conversation() - Session created: ...
    ✓ get_current_section() - Section: IDENTIFICATION
    ✓ save_turn() - Response recorded
    ✓ State machine enforcement
    ✓ resume_conversation() - Retrieved X turns

[2] Testing DocumentService...
    ✓ validate_file() - File validation
    ✓ upload_document() - Document upload
    ✓ extract_text() - Text extraction
    ✓ store_extract() - Entity persistence
    ✓ list_session_documents() - Documents: X

[3] Testing Integration...
    ✓ Audit logging - X audit events recorded
    ✓ State machine verification

======================================================================
✓ ALL SERVICE LAYER TESTS PASSED
======================================================================
```

---

## Integration Points

### With Repositories (Prompt 3)
- Services use repository pattern for all data access
- No direct model manipulation
- CRUD operations go through repositories

### With Models (Prompt 1)
- Services persist to SessionModel, DocumentModel, ConversationTurnModel, ExtractedEntityModel, AuditLogModel
- All relationships properly maintained

### With Schemas (Pydantic)
- All inputs validated against Pydantic schemas
- All outputs wrapped in response schemas
- Type safety throughout

---

## Configuration

### Settings
```python
from app.core.config import settings

# File upload directory
settings.upload_dir  # Default: ./uploads

# Max file size (bytes)
settings.max_upload_size_bytes  # Default: 26214400 (25MB)

# LLM provider
settings.llm_provider  # "openai", "ollama", "mock"
```

---

## Next Steps: Prompt 5

Create FastAPI endpoints:
```python
# conversations.py
@router.post("/conversations")
async def create_conversation(...)

@router.post("/conversations/{session_id}/responses")
async def submit_response(...)

# documents.py
@router.post("/sessions/{session_id}/documents")
async def upload_document(...)

@router.get("/sessions/{session_id}/documents")
async def list_documents(...)
```

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `backend/app/modules/conversation/service.py` | ClinicalConversationService |
| `backend/app/modules/conversation/state_machine.py` | Section/SOCRATES progression |
| `backend/app/modules/documents/service.py` | DocumentService |
| `backend/app/modules/documents/lab_rules.py` | Lab abnormality detection |
| `backend/test_service_layer.py` | Service layer tests |

---

## Support

See documentation files:
- `SERVICE_LAYER_VERIFICATION.md` — Full method verification
- `FINAL_CHECKLIST_PROMPT_4.md` — Complete requirement checklist
- `PROMPT_4_COMPLETION_REPORT.md` — Architecture overview

---

**Prompt 4: Service Layer** — Status: ✓ COMPLETE
