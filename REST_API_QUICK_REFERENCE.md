# REST API QUICK REFERENCE

## Base URL
```
http://localhost:8000
```

## Conversation Endpoints

### Create Session
```
POST /sessions/
{
  "patient_id": "uuid-string",
  "mode": "MODERN|AYUSH",
  "disclaimer_acknowledged": true
}
→ 201: SessionStateResponse
```

### Get Session State
```
GET /sessions/{session_id}
→ 200: SessionStateResponse
```

### Acknowledge Disclaimer
```
POST /sessions/{session_id}/disclaimer
{
  "acknowledged": true
}
→ 200: SessionStateResponse
```

### Submit Response & Advance
```
POST /sessions/{session_id}/responses
{
  "text": "patient response text"
}
→ 200: ProcessResponseResult
```

### Get Conversation History
```
GET /sessions/{session_id}/conversation
→ 200: List[TurnResponse]
```

---

## Document Endpoints

### Upload Document
```
POST /sessions/{session_id}/documents
Content-Type: multipart/form-data
file: <PDF|PNG|JPEG>
→ 201: DocumentUploadResponse
```

### List Documents
```
GET /sessions/{session_id}/documents
→ 200: DocumentListResponse
```

### Get Document
```
GET /sessions/{session_id}/documents/{document_id}
→ 200: DocumentUploadResponse
```

### Get Entities
```
GET /sessions/{session_id}/entities?abnormal_only=true
→ 200: EntityListResponse
```

### Delete Document
```
DELETE /sessions/{session_id}/documents/{document_id}
→ 200: DocumentDeleteResponse
```

---

## Summary Endpoints

### Generate Summary
```
POST /sessions/{session_id}/summaries
{
  "include_recommendations": true,
  "include_abnormalities_only": false
}
→ 201: ClinicalSummaryResponse
```

### Get Summary
```
GET /sessions/{session_id}/summaries/{summary_id}
→ 200: ClinicalSummaryResponse
```

---

## Consent Endpoints

### Log Consent
```
POST /sessions/{session_id}/consent/log
{
  "action": "ACKNOWLEDGED|REVOKED",
  "consent_type": "DATA_SHARING",
  "details": {}
}
→ 201: ConsentLogResponse
```

### Get Consent History
```
GET /patients/{patient_id}/consent/history
→ 200: ConsentHistoryResponse
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Validation error |
| 403 | Forbidden |
| 404 | Not found |
| 413 | File too large |
| 415 | Invalid MIME type |
| 500 | Server error |

---

## Error Format

```json
{
  "error": "Description",
  "code": "ERROR_CODE",
  "status": 400,
  "request_id": "req-123"
}
```

---

## Common Error Codes

- `SESSION_NOT_FOUND`
- `DISCLAIMER_NOT_ACKNOWLEDGED`
- `FILE_TOO_LARGE`
- `UNSUPPORTED_MEDIA_TYPE`
- `VALIDATION_ERROR`
- `EXTRACTION_FAILED`
- `DATABASE_ERROR`

---

## Python Example

```python
import requests

BASE = "http://localhost:8000"

# Create session
r = requests.post(f"{BASE}/sessions/", json={
    "patient_id": "abc-123",
    "mode": "MODERN",
    "disclaimer_acknowledged": True
})
session_id = r.json()["session_id"]

# Submit response
r = requests.post(f"{BASE}/sessions/{session_id}/responses", json={
    "text": "I have chest pain"
})

# Get history
r = requests.get(f"{BASE}/sessions/{session_id}/conversation")
```

---

## Curl Examples

### Create Session
```bash
curl -X POST http://localhost:8000/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "abc-123",
    "mode": "MODERN",
    "disclaimer_acknowledged": true
  }'
```

### Upload Document
```bash
curl -X POST http://localhost:8000/sessions/xyz-789/documents \
  -F "file=@lab_report.pdf"
```

### Get Session
```bash
curl http://localhost:8000/sessions/xyz-789
```

---

## Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

---

## Architecture

```
FastAPI App
    ↓
V1 APIRouter
    ├── Conversation Router (/sessions)
    ├── Documents Router (/sessions)
    ├── Summary Router (/sessions)
    ├── Consent Router (/sessions, /patients)
    └── Health Router (/health)
```

---

## Key Features

✓ All endpoints validated with Pydantic  
✓ Standard HTTP status codes  
✓ Custom error codes for debugging  
✓ Audit logging (no patient content)  
✓ Request ID tracing  
✓ CORS enabled  
✓ Auto-generated documentation  
✓ Production-ready error handling  

---

## Status

**Implementation:** ✓ COMPLETE  
**Testing:** ✓ READY  
**Documentation:** ✓ READY  
**Production:** ✓ READY
