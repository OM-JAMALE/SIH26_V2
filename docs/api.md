# Healthcare AI Platform - REST API Documentation

Comprehensive REST API reference for the Healthcare AI Pre-Consultation and History Digitization Platform.

---

## 1. Global Specifications

- **Base URL**: `http://localhost:8000/api/v1`
- **Data Interchange Format**: JSON (`application/json`)
- **Multipart Uploads**: `multipart/form-data` for medical document uploads
- **Error Response Envelope**:
  ```json
  {
    "detail": {
      "error": "Human readable error description",
      "code": "ERROR_SPECIFIC_CODE",
      "details": null
    }
  }
  ```

---

## 2. Health & System Endpoints

### `GET /health`
Returns process liveness status.

- **Response `200 OK`**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-09-12T00:50:00Z"
  }
  ```

### `GET /api/v1/status`
Returns database, cache, and AI provider readiness.

- **Response `200 OK`**:
  ```json
  {
    "status": "ready",
    "database": "connected",
    "redis": "connected",
    "ai_provider": "mock"
  }
  ```

---

## 3. Patient & Consultation Session Endpoints

### `POST /api/v1/sessions`
Initializes a new patient consultation session.

- **Request Body**:
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1988-06-15",
    "gender": "male",
    "mode": "MODERN",
    "disclaimer_acknowledged": true
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "session_id": "4c8e7294-09cc-463c-bf71-73db6a09883c",
    "patient_id": "1837d41d-7259-4d30-9547-2e659c12e8c5",
    "status": "INITIATED",
    "current_section": "CHIEF_COMPLAINT",
    "socrates_state": "SITE",
    "created_at": "2026-09-12T00:50:00Z"
  }
  ```

### `GET /api/v1/sessions/{session_id}`
Retrieves active session state and progress.

- **Response `200 OK`**:
  ```json
  {
    "id": "4c8e7294-09cc-463c-bf71-73db6a09883c",
    "status": "IN_CONVERSATION",
    "current_section": "SOCRATES",
    "socrates_state": "ONSET",
    "safety_status": "SAFE"
  }
  ```

---

## 4. Module A: Conversational History Engine

### `POST /api/v1/sessions/{session_id}/turns`
Submits a patient natural language turn and returns the next adaptive conversational query.

- **Request Body**:
  ```json
  {
    "content": "I have severe crushing pain in the middle of my chest."
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "turn_index": 1,
    "speaker": "AI",
    "response_text": "Did this chest pain start suddenly or build up gradually?",
    "current_section": "SOCRATES",
    "socrates_state": "ONSET",
    "safety_alert": null,
    "is_completed": false
  }
  ```

- **Emergency Triage Trigger (`200 OK` with Safety Escalation)**:
  ```json
  {
    "turn_index": 2,
    "speaker": "AI",
    "response_text": "CRITICAL EMERGENCY DETECTED: Based on red-flag symptoms, please call emergency services immediately.",
    "current_section": "COMPLETED",
    "safety_alert": {
      "is_red_flag": true,
      "alert_level": "ESCALATE_EMERGENCY",
      "matched_triggers": ["crushing chest pain", "shortness of breath"]
    },
    "is_completed": true
  }
  ```

### `GET /api/v1/sessions/{session_id}/history`
Retrieves full chronological dialogue turns for a session.

---

## 5. Module B: Medical Document Digitization

### `POST /api/v1/sessions/{session_id}/documents`
Uploads a medical laboratory report (PDF, PNG, JPEG, size limit 10MB).

- **Form Data**:
  - `file`: binary file payload
- **Response `201 Created`**:
  ```json
  {
    "id": "doc-991823",
    "session_id": "4c8e7294-09cc-463c-bf71-73db6a09883c",
    "filename": "blood_report.pdf",
    "status": "ANALYZED",
    "extracted_entities": [
      {
        "entity_name": "Hemoglobin",
        "value": "9.2",
        "unit": "g/dL",
        "reference_range": "12.0 - 16.0",
        "is_abnormal": true
      }
    ]
  }
  ```

---

## 6. Module C: Structured Clinical Summary

### `POST /api/v1/sessions/{session_id}/summary`
Triggers bounded LLM summary generation with Pydantic validation.

- **Response `201 Created`**:
  ```json
  {
    "id": "sum-10293",
    "session_id": "4c8e7294-09cc-463c-bf71-73db6a09883c",
    "workflow_status": "PHYSICIAN_REVIEW",
    "structured_summary": {
      "chief_complaint": [{"name": "Chest Pain", "status": "KNOWN"}],
      "generated_summary_text": "38yo male presents with acute retrosternal chest pain."
    }
  }
  ```

### `PATCH /api/v1/sessions/{session_id}/summary`
Proposes physician edits to the summary while preserving original AI output.

### `POST /api/v1/sessions/{session_id}/summary/accept`
Physician approves and finalizes the summary.

### `POST /api/v1/sessions/{session_id}/summary/reject`
Physician rejects summary and requests re-extraction.

---

## 7. Module D: Integrations & Patient Consent

### `POST /api/v1/sessions/{session_id}/consent`
Records patient explicit consent grant or revocation.

- **Request Body**:
  ```json
  {
    "patient_id": "1837d41d-7259-4d30-9547-2e659c12e8c5",
    "granted": true,
    "terms_version": "v1.0"
  }
  ```

### `GET /api/v1/sessions/{session_id}/fhir/diagnostic-report`
Exports consultation session as an HL7 FHIR R4 `DiagnosticReport` bundle.

### `GET /api/v1/sessions/{session_id}/abdm/bundle`
Exports ABDM HIP compliant payload linked to ABHA ID.
