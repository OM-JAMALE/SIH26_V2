# REST API ENDPOINTS - COMPLETE IMPLEMENTATION GUIDE

## Status: ✓ IMPLEMENTATION COMPLETE (Module Routers Architecture)

---

## Architecture Overview

The REST API is implemented using a **modular router architecture**:

```
FastAPI App (main.py)
    ↓
APIRouter (api/v1/router.py)
    ├── Health Router (/health)
    ├── Conversation Router (/sessions)
    ├── Documents Router (/sessions)
    └── Summary Router (/sessions)
```

---

## API Endpoints

### Module A: Conversation Endpoints

**Base Path:** `/sessions`

#### 1. Create New Conversation Session
```http
POST /sessions/
Content-Type: application/json

{
  "patient_id": "abc-123",
  "mode": "MODERN",
  "disclaimer_acknowledged": true
}
```

**Response (201 Created):**
```json
{
  "session_id": "xyz-789",
  "patient_id": "abc-123",
  "lifecycle_status": "IN_PROGRESS",
  "current_section": "IDENTIFICATION",
  "disclaimer_acknowledged": true,
  "latest_question": "Welcome to the clinical interview..."
}
```

**Error Cases:**
- 400: Invalid patient_id or mode
- 500: Database error

#### 2. Acknowledge Disclaimer
```http
POST /sessions/{session_id}/disclaimer
Content-Type: application/json

{
  "acknowledged": true
}
```

**Response (200 OK):**
```json
{
  "session_id": "xyz-789",
  "lifecycle_status": "IN_PROGRESS",
  "disclaimer_acknowledged": true
}
```

**Error Cases:**
- 404: Session not found
- 400: Invalid payload

#### 3. Get Conversation State
```http
GET /sessions/{session_id}
```

**Response (200 OK):**
```json
{
  "session_id": "xyz-789",
  "patient_id": "abc-123",
  "lifecycle_status": "IN_PROGRESS",
  "mode": "MODERN",
  "current_section": "HPI",
  "socrates_state": "SITE",
  "latest_question": "Can you describe the location of the pain?",
  "structured_history": {
    "chief_complaint": [...],
    "hpi_socrates": {...}
  },
  "safety": {
    "flagged": false,
    "alerts": []
  }
}
```

**Error Cases:**
- 404: Session not found
- 500: Database error

#### 4. Submit User Response & Advance Section
```http
POST /sessions/{session_id}/responses
Content-Type: application/json

{
  "text": "The pain is in my chest, on the left side"
}
```

**Response (200 OK):**
```json
{
  "session_id": "xyz-789",
  "lifecycle_status": "IN_PROGRESS",
  "current_section": "HPI",
  "socrates_state": "ONSET",
  "next_question": "When did the pain start?",
  "structured_updates": {
    "extracted_symptoms": [
      {
        "symptom": "chest pain",
        "status": "PRESENT",
        "location": "left side"
      }
    ]
  },
  "safety": {
    "flagged": false
  }
}
```

**Error Cases:**
- 404: Session not found
- 403: Disclaimer not acknowledged
- 400: Session not in progress (completed/escalated)
- 500: Extraction or state machine error

#### 5. Get Conversation History
```http
GET /sessions/{session_id}/conversation
```

**Response (200 OK):**
```json
[
  {
    "turn_index": 1,
    "speaker": "SYSTEM",
    "content": "Welcome to the clinical interview...",
    "section": "IDENTIFICATION",
    "created_at": "2024-01-15T10:00:00Z"
  },
  {
    "turn_index": 2,
    "speaker": "PATIENT",
    "content": "I have chest pain",
    "extracted_data": {...},
    "section": "CHIEF_COMPLAINT",
    "created_at": "2024-01-15T10:01:00Z"
  },
  ...
]
```

**Error Cases:**
- 404: Session not found
- 500: Database error

---

### Module B: Document Endpoints

**Base Path:** `/sessions/{session_id}/documents`

#### 1. Upload & Process Document
```http
POST /sessions/{session_id}/documents
Content-Type: multipart/form-data

file: <PDF|PNG|JPEG file>
```

**Response (201 Created):**
```json
{
  "document_id": "doc-123",
  "session_id": "xyz-789",
  "filename": "lab_report.pdf",
  "mime_type": "application/pdf",
  "file_size": 245632,
  "processing_status": "EXTRACTED",
  "extracted_entities": [
    {
      "entity_type": "LAB_RESULT",
      "entity_name": "Hemoglobin",
      "value": "14.5 g/dL",
      "numeric_value": 14.5,
      "unit": "g/dL",
      "reference_range": "13.0-17.5",
      "is_abnormal": false,
      "confidence_score": 0.97
    }
  ],
  "created_at": "2024-01-15T10:15:00Z"
}
```

**Error Cases:**
- 404: Session not found
- 415: Unsupported MIME type
- 413: File too large (>25MB)
- 400: Invalid file
- 500: Extraction error

#### 2. List Session Documents
```http
GET /sessions/{session_id}/documents
```

**Response (200 OK):**
```json
{
  "total": 2,
  "documents": [
    {
      "document_id": "doc-123",
      "filename": "lab_report.pdf",
      "processing_status": "EXTRACTED",
      "created_at": "2024-01-15T10:15:00Z"
    },
    {
      "document_id": "doc-456",
      "filename": "prescription.jpg",
      "processing_status": "EXTRACTED",
      "created_at": "2024-01-15T10:20:00Z"
    }
  ]
}
```

**Error Cases:**
- 404: Session not found
- 500: Database error

#### 3. Get Document Details
```http
GET /sessions/{session_id}/documents/{document_id}
```

**Response (200 OK):**
```json
{
  "document_id": "doc-123",
  "filename": "lab_report.pdf",
  "processing_status": "EXTRACTED",
  "extracted_entities": [
    {
      "entity_id": "ent-789",
      "entity_type": "LAB_RESULT",
      "entity_name": "Glucose",
      "value": "245 mg/dL",
      "numeric_value": 245.0,
      "is_abnormal": true,
      "confidence_score": 0.99
    }
  ]
}
```

**Error Cases:**
- 404: Session or document not found
- 500: Database error

#### 4. Get Extracted Entities
```http
GET /sessions/{session_id}/entities?abnormal_only=true
```

**Response (200 OK):**
```json
{
  "total": 3,
  "entities": [
    {
      "entity_id": "ent-123",
      "entity_type": "LAB_RESULT",
      "entity_name": "Glucose",
      "value": "245 mg/dL",
      "is_abnormal": true,
      "severity": "HIGH",
      "document_id": "doc-123"
    }
  ]
}
```

**Query Parameters:**
- `abnormal_only` (bool): Filter to abnormal only
- `entity_type` (str): Filter by type

**Error Cases:**
- 404: Session not found
- 500: Database error

#### 5. Delete Document
```http
DELETE /sessions/{session_id}/documents/{document_id}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Document and associated entities deleted successfully",
  "document_id": "doc-123"
}
```

**Error Cases:**
- 404: Session or document not found
- 500: Database error

---

### Module C: Summary Endpoints

**Base Path:** `/sessions/{session_id}/summaries`

#### 1. Generate Clinical Summary
```http
POST /sessions/{session_id}/summaries
Content-Type: application/json

{
  "include_recommendations": true,
  "include_abnormalities_only": false
}
```

**Response (201 Created):**
```json
{
  "summary_id": "sum-123",
  "session_id": "xyz-789",
  "chief_complaint": "Chest pain",
  "generated_summary_text": "Patient presents with acute retrosternal chest pain onset 2 hours ago...",
  "key_findings": [
    {
      "name": "Elevated Troponin",
      "value": "0.04 ng/mL",
      "is_abnormal": true
    }
  ],
  "red_flags": [
    {
      "flag_name": "ACUTE_CHEST_PAIN",
      "description": "Acute chest discomfort requires urgent evaluation",
      "severity": "CRITICAL"
    }
  ],
  "recommendations": [
    "Immediate ECG",
    "Cardiology consultation",
    "Monitor vital signs"
  ],
  "uncertainty_notes": [
    "Exact lipid panel not provided",
    "Recent ECG baseline not available"
  ]
}
```

**Error Cases:**
- 404: Session not found
- 400: Session not complete/ready
- 500: LLM error or database error

#### 2. Get Summary
```http
GET /sessions/{session_id}/summaries/{summary_id}
```

**Response (200 OK):**
```json
{
  "summary_id": "sum-123",
  "session_id": "xyz-789",
  "generated_summary_text": "Patient presents with...",
  "created_at": "2024-01-15T10:45:00Z"
}
```

**Error Cases:**
- 404: Session or summary not found
- 500: Database error

---

### Module D: Consent Endpoints

**Base Path:** `/sessions/{session_id}/consent`

#### 1. Log Consent Action
```http
POST /sessions/{session_id}/consent/log
Content-Type: application/json

{
  "action": "ACKNOWLEDGED",
  "consent_type": "DATA_SHARING",
  "details": {
    "scope": "HIMS_ONLY",
    "duration_days": 365
  }
}
```

**Response (201 Created):**
```json
{
  "consent_id": "con-123",
  "session_id": "xyz-789",
  "action": "ACKNOWLEDGED",
  "consent_type": "DATA_SHARING",
  "timestamp": "2024-01-15T10:00:00Z",
  "is_immutable": true
}
```

**Error Cases:**
- 404: Session not found
- 400: Invalid action or consent_type
- 500: Database error

#### 2. Get Consent History
```http
GET /patients/{patient_id}/consent/history
```

**Response (200 OK):**
```json
{
  "patient_id": "abc-123",
  "total_records": 5,
  "records": [
    {
      "consent_id": "con-123",
      "action": "ACKNOWLEDGED",
      "consent_type": "DATA_SHARING",
      "timestamp": "2024-01-15T10:00:00Z",
      "session_id": "xyz-789"
    },
    {
      "consent_id": "con-124",
      "action": "REVOKED",
      "consent_type": "DATA_SHARING",
      "timestamp": "2024-01-20T14:00:00Z",
      "session_id": "xyz-789"
    }
  ]
}
```

**Error Cases:**
- 404: Patient not found
- 500: Database error

**Note:** Consent records are immutable (never deleted)

---

## Error Handling

### Standard Error Response
```json
{
  "error": "Descriptive error message",
  "code": "ERROR_CODE",
  "status": 400,
  "request_id": "req-123-abc"
}
```

### Common Status Codes
- **200 OK** — Success
- **201 Created** — Resource created
- **400 Bad Request** — Validation error
- **403 Forbidden** — Denied (disclaimer not acknowledged)
- **404 Not Found** — Resource not found
- **413 Payload Too Large** — File too large
- **415 Unsupported Media Type** — Invalid file type
- **500 Internal Server Error** — Server error

### Error Codes
- `SESSION_NOT_FOUND` — Session doesn't exist
- `DISCLAIMER_NOT_ACKNOWLEDGED` — Disclaimer not accepted
- `UNSUPPORTED_MEDIA_TYPE` — Invalid MIME type
- `FILE_TOO_LARGE` — Exceeds 25MB limit
- `VALIDATION_ERROR` — Invalid request data
- `EXTRACTION_FAILED` — Document extraction error
- `DATABASE_ERROR` — Database operation failed

---

## Audit Logging

All sensitive operations log audit events (WITHOUT patient content):

**Logged Events:**
- SESSION_CREATED
- PATIENT_RESPONSE_RECEIVED
- STATE_TRANSITION
- SAFETY_ESCALATED
- DOCUMENT_UPLOADED
- DOCUMENT_EXTRACTED
- SUMMARY_GENERATED
- CONSENT_LOGGED
- CONSENT_REVOKED

**Logged Information:**
- ✓ Timestamp
- ✓ Action type
- ✓ Session/Patient ID (UUID, not PII)
- ✓ Request ID (for tracing)
- ✓ Status (SUCCESS/FAILED)

**NOT Logged:**
- ✗ Patient names
- ✗ Symptoms or medical details
- ✗ Lab values
- ✗ Medications
- ✗ Any clinical content

---

## Request/Response Schemas

### Conversation Schemas

**CreateSessionRequest:**
```python
{
  "patient_id": str,  # UUID as string
  "mode": "MODERN" | "AYUSH",
  "disclaimer_acknowledged": bool
}
```

**SubmitResponseRequest:**
```python
{
  "text": str  # Patient response (1-10000 chars)
}
```

**AcknowledgeDisclaimerRequest:**
```python
{
  "acknowledged": bool
}
```

### Document Schemas

**DocumentUploadResponse:**
```python
{
  "document_id": str,
  "session_id": str,
  "filename": str,
  "mime_type": str,
  "file_size": int,
  "processing_status": "PENDING" | "EXTRACTED" | "FAILED",
  "extracted_entities": List[ExtractedEntity],
  "created_at": datetime
}
```

### Summary Schemas

**GenerateSummaryRequest:**
```python
{
  "include_recommendations": bool,
  "include_abnormalities_only": bool
}
```

### Consent Schemas

**LogConsentRequest:**
```python
{
  "action": "ACKNOWLEDGED" | "REVOKED",
  "consent_type": str,
  "details": dict  # Optional metadata
}
```

---

## Authentication & Security

### Request ID Middleware
All requests receive unique ID for tracing:
```
Header: X-Request-ID: req-abc-123
```

### CORS Configuration
```python
allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
allow_credentials = True
allow_methods = ["*"]
allow_headers = ["*"]
```

### Input Validation
- Pydantic schemas validate all inputs
- UUID validation on all IDs
- File type and size validation
- String length validation

---

## Usage Examples

### Example 1: Complete Conversation Flow
```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create session
response = requests.post(
    f"{BASE_URL}/sessions/",
    json={
        "patient_id": "abc-123",
        "mode": "MODERN",
        "disclaimer_acknowledged": True
    }
)
session = response.json()
session_id = session["session_id"]

# 2. Get current state
response = requests.get(f"{BASE_URL}/sessions/{session_id}")
state = response.json()
print(f"Current section: {state['current_section']}")
print(f"Question: {state['latest_question']}")

# 3. Submit response
response = requests.post(
    f"{BASE_URL}/sessions/{session_id}/responses",
    json={"text": "I have chest pain"}
)
result = response.json()
print(f"Next section: {result['current_section']}")

# 4. Get history
response = requests.get(f"{BASE_URL}/sessions/{session_id}/conversation")
history = response.json()
print(f"Total turns: {len(history)}")
```

### Example 2: Document Upload & Processing
```python
# Upload document
with open("lab_report.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/documents",
        files=files
    )
    doc = response.json()
    print(f"Processing status: {doc['processing_status']}")
    print(f"Extracted entities: {len(doc['extracted_entities'])}")

# Get abnormal results
response = requests.get(
    f"{BASE_URL}/sessions/{session_id}/entities?abnormal_only=true"
)
abnormal = response.json()
for entity in abnormal["entities"]:
    print(f"{entity['entity_name']}: {entity['value']} (severity: {entity['severity']})")
```

### Example 3: Consent Tracking
```python
# Log consent
response = requests.post(
    f"{BASE_URL}/sessions/{session_id}/consent/log",
    json={
        "action": "ACKNOWLEDGED",
        "consent_type": "DATA_SHARING",
        "details": {"scope": "HIMS_ONLY", "duration_days": 365}
    }
)

# Get consent history
response = requests.get(f"{BASE_URL}/patients/abc-123/consent/history")
history = response.json()
for record in history["records"]:
    print(f"{record['action']} - {record['timestamp']}")
```

---

## Testing

### Run API Tests
```bash
cd backend
python -m pytest tests/test_api.py -v
```

### Manual Testing with curl
```bash
# Create session
curl -X POST http://localhost:8000/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"abc-123","mode":"MODERN","disclaimer_acknowledged":true}'

# Get session state
curl http://localhost:8000/sessions/xyz-789

# Upload document
curl -X POST http://localhost:8000/sessions/xyz-789/documents \
  -F "file=@lab_report.pdf"
```

---

## Documentation

### API Documentation (Auto-generated)
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### OpenAPI Schema
- JSON: `http://localhost:8000/openapi.json`

---

## Summary

✓ **Conversation Endpoints** (5 endpoints)
✓ **Document Endpoints** (5 endpoints)
✓ **Summary Endpoints** (2 endpoints)
✓ **Consent Endpoints** (2 endpoints)
✓ **Error Handling** (Standard HTTP + custom codes)
✓ **Audit Logging** (No patient content)
✓ **Request/Response Schemas** (Pydantic)
✓ **Auto Documentation** (Swagger + ReDoc)

**Status: PRODUCTION READY** ✓
