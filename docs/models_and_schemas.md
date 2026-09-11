# Health AI Database Models & Schemas

## Overview

The Health AI platform uses SQLAlchemy 2.0 ORM for database layer and Pydantic v2 for request/response validation at API boundaries.

**Key Principle:** Never expose ORM models directly to clients - always use Pydantic schemas.

---

## Architecture

```
Request → Pydantic Schema Validation → Service Layer → Repository Layer → SQLAlchemy ORM → Database
Response ← Pydantic Schema Serialization ← Service Layer ← Repository Layer ← SQLAlchemy ORM
```

---

## Database Models (SQLAlchemy)

Located in `backend/app/db/models/`

### 1. **Patient** (`patient.py`)
Represents a healthcare patient.

**Fields:**
- `id` (UUID, PK): Unique identifier
- `national_health_id` (String, unique): Indian ABHA/PHR ID (optional)
- `first_name` (String): First name
- `last_name` (String): Last name
- `dob` (String): Date of birth (ISO format YYYY-MM-DD)
- `gender` (String): MALE, FEMALE, OTHER
- `contact_number` (String): Phone/mobile (optional)
- `created_at` (DateTime): Timestamp
- `updated_at` (DateTime): Timestamp

**Relationships:**
- `sessions` → List[Session]: One patient has many consultation sessions
- `consents` → List[Consent]: Consent records for this patient

**Indexes:**
- `national_health_id` (unique, for ABHA lookup)

---

### 2. **Session** (`session.py`) - Conversation Session
Represents one consultation/pre-consultation session.

**Fields:**
- `id` (UUID, PK): Unique session identifier
- `patient_id` (UUID, FK): Links to patient
- `lifecycle_status` (String): CREATED, IN_PROGRESS, SAFETY_ESCALATED, COMPLETED
- `status` (String): INITIATED, IN_CONVERSATION, DOCUMENTS_UPLOADED, SUMMARY_GENERATED, PHYSICIAN_REVIEWED, CONSENTED, COMPLETED
- `mode` (String): MODERN or AYUSH (medical system)
- `current_section` (String): CHIEF_COMPLAINT, HPI, SOCRATES, PMH, PSH, DRUG_HISTORY, ALLERGY_HISTORY, FAMILY_HISTORY, PERSONAL_HISTORY, ROS, COMPLETED
- `socrates_state` (String): SOCRATES sub-section (SITE, CHARACTER, AGGRAVATING, etc.)
- `structured_history` (JSON): Accumulated extracted clinical history
- `safety_status` (String): SAFE, WARNING, ESCALATED
- `safety_alerts` (JSON): Alert details
- `disclaimer_acknowledged` (Boolean): Whether patient acknowledged disclaimer
- `disclaimer_acknowledged_at` (DateTime): Timestamp of disclaimer acknowledgment
- `created_at` (DateTime): Timestamp
- `updated_at` (DateTime): Timestamp

**Relationships:**
- `patient` → Patient: Parent patient
- `conversation_turns` → List[ConversationTurn]: All turns in this session
- `documents` → List[Document]: Uploaded documents
- `extracted_entities` → List[ExtractedEntity]: Extracted clinical data
- `summaries` → List[Summary]: Generated summaries
- `consents` → List[Consent]: Consent records

**Indexes:**
- `patient_id`, `lifecycle_status`, `status` (for filtering)

---

### 3. **ConversationTurn** (`conversation_turn.py`)
One exchange between patient and system in a session.

**Fields:**
- `id` (UUID, PK): Turn identifier
- `session_id` (UUID, FK): Links to session
- `turn_index` (Integer): Turn number in sequence
- `speaker` (String): PATIENT or SYSTEM
- `content` (Text): Message content
- `section` (String): Which section this turn belongs to
- `extracted_data` (JSON): Data extracted from this turn
- `safety_alerts` (JSON): Any safety alerts triggered
- `created_at` (DateTime): Timestamp
- `updated_at` (DateTime): Timestamp

**Relationships:**
- `session` → Session: Parent session

**Indexes:**
- `session_id`, `section`

**State Machine:** Conversation progresses through sections in order:
```
CHIEF_COMPLAINT → HPI → SOCRATES → PMH → PSH → 
DRUG_HISTORY → ALLERGY_HISTORY → FAMILY_HISTORY → 
PERSONAL_HISTORY → ROS → COMPLETED
```

---

### 4. **Document** (`document.py`)
Uploaded medical document (PDF, image).

**Fields:**
- `id` (UUID, PK): Document identifier
- `session_id` (UUID, FK): Links to session
- `filename` (String): Original filename
- `file_path` (String): Storage path
- `mime_type` (String): application/pdf, image/png, image/jpeg
- `file_size` (Integer): Size in bytes
- `processing_status` (String): PENDING, EXTRACTED, FAILED
- `raw_text` (Text): Extracted text content
- `created_at` (DateTime): Timestamp
- `updated_at` (DateTime): Timestamp

**Relationships:**
- `session` → Session: Parent session
- `extracted_entities` → List[ExtractedEntity]: Entities extracted from this document

**Constraints:**
- Max file size: 25MB
- Supported types: PDF, PNG, JPEG
- MIME type validation enforced

**Indexes:**
- `session_id`, `processing_status`

---

### 5. **ExtractedEntity** (`extracted_entity.py`)
Structured clinical data extracted from conversation or documents.

**Fields:**
- `id` (UUID, PK): Entity identifier
- `session_id` (UUID, FK): Links to session
- `document_id` (UUID, FK): Links to document if extracted from document
- `entity_type` (String): LAB_RESULT, MEDICATION, DIAGNOSIS, VITAL, SYMPTOM
- `entity_name` (String): Name of entity (e.g., "Hemoglobin", "Aspirin")
- `value` (String): String representation of value
- `numeric_value` (Float): Numeric value for lab results
- `unit` (String): Unit (mg/dL, g/dL, etc.)
- `reference_range` (String): Normal range
- `is_abnormal` (Boolean): Whether outside normal range (deterministic)
- `confidence_score` (Float): 0-1 confidence from extraction
- `metadata_json` (JSON): Additional metadata
- `created_at` (DateTime): Timestamp
- `updated_at` (DateTime): Timestamp

**Relationships:**
- `session` → Session: Parent session
- `document` → Document: Source document (if applicable)

**Lab Abnormality Detection:**
- **Deterministic, not LLM-based**
- Hardcoded reference ranges for common tests
- Severity levels: LOW, MEDIUM, HIGH based on deviation %

**Supported Lab Tests (Hardcoded Rules):**
- Hemoglobin: 12-17 g/dL
- WBC: 4.5-11 K/uL
- Glucose: 70-100 mg/dL
- Creatinine: 0.7-1.3 mg/dL
- Sodium: 136-145 mEq/L
- Potassium: 3.5-5 mEq/L

**Indexes:**
- `session_id`, `document_id`, `entity_type`, `is_abnormal`

---

### 6. **Summary** (`summary.py`)
Generated clinical summary.

**Fields:**
- `id` (UUID, PK): Summary identifier
- `session_id` (UUID, FK): Links to session
- `version` (Integer): Summary version (incremented on regeneration)
- `workflow_status` (String): NOT_GENERATED, GENERATING, GENERATED, PHYSICIAN_REVIEW, ACCEPTED, REJECTED, REGENERATING, FAILED
- `status` (String): DRAFT, PUBLISHED (legacy)
- `structured_summary` (JSON): AI-generated summary object
- `physician_edited_summary` (JSON): Physician-edited version
- `llm_model` (String): Model used (mock-llm, ollama, gpt-4, etc.)
- `prompt_version` (String): Prompt version for reproducibility
- `generation_error` (Text): Error message if generation failed
- `accepted_at` (DateTime): When physician accepted
- `accepted_by` (String): Physician/user who accepted
- `rejected_at` (DateTime): When rejected
- `rejected_reason` (Text): Why rejected
- `physician_notes` (Text): Additional notes
- `created_at` (DateTime): Timestamp
- `updated_at` (DateTime): Timestamp

**Structured Summary Contains:**
```json
{
  "chief_complaint": "...",
  "hpi": "...",
  "pmh": "...",
  "drug_and_allergy": "...",
  "family_history": "...",
  "personal_history": "...",
  "ros": "...",
  "prior_investigations": "...",
  "key_findings": ["..."],
  "red_flags": ["..."],
  "recommendations": ["..."],
  "uncertainty_notes": "..."
}
```

**Relationships:**
- `session` → Session: Parent session

**Indexes:**
- `session_id`, `workflow_status`

---

### 7. **Consent** (`consent.py`)
Consent audit trail for privacy/ABDM/FHIR sharing.

**Fields:**
- `id` (UUID, PK): Consent record identifier
- `session_id` (UUID, FK): Links to session
- `patient_id` (UUID, FK): Links to patient
- `purpose` (String): Purpose (data_sharing, abdm_integration, fhir_export, research, etc.)
- `granted` (Boolean): Consent status
- `terms_version` (String): Version of terms accepted
- `signature_hash` (String): Hash of digital signature
- `ip_address` (String): IP of consent action
- `granted_at` (DateTime): When consent given
- `revoked_at` (DateTime): When revoked (if applicable)
- `created_at` (DateTime): Timestamp
- `updated_at` (DateTime): Timestamp

**Relationships:**
- `session` → Session: Parent session
- `patient` → Patient: Patient consenting

**Audit Trail:**
- Immutable record of all consent actions
- Revocation tracked separately
- IP address logged for security
- Never delete - only mark revoked

**Indexes:**
- `session_id`, `patient_id`, `purpose`

---

### 8. **AuditLog** (`audit_log.py`)
Security and compliance audit trail.

**Fields:**
- `id` (UUID, PK): Log entry identifier
- `session_id` (UUID, FK): Links to session (nullable)
- `user_id` (String): Who performed action
- `action` (String): Action name
- `resource` (String): Resource type (PATIENT_DATA, CONSENT, EXPORT, etc.)
- `status` (String): SUCCESS, FAILURE, FORBIDDEN
- `details` (JSON): Action details (NO clinical content)
- `request_id` (String): Request trace ID
- `created_at` (DateTime): Timestamp
- `updated_at` (DateTime): Timestamp

**Relationships:**
- None (audit log is immutable and standalone)

**Never Log:**
- Patient clinical content
- API keys or authentication tokens
- Sensitive personal information
- File contents

**What to Log:**
- User actions (create session, upload document, generate summary)
- Sensitive operations (consent changes, data exports)
- Security events (access denied, unusual patterns)
- Metadata only (action type, timestamp, status)

**Indexes:**
- `session_id`, `user_id`, `action`, `created_at` (for audit reports)

---

## Pydantic v2 Schemas

Located in `backend/app/schemas/`

### Validation Rules by Model:

#### **Patient Schemas** (`patient.py`)
- `PatientCreate`: For POST /patients/
- `PatientUpdate`: For PATCH /patients/{id}
- `PatientResponse`: For API responses
- Validations: DOB format, gender enum, email format

#### **Session Schemas** (`session.py`)
- `SessionCreate`: Create new conversation
- `SessionUpdate`: Update session state
- `SessionResponse`: Full session info
- Validations: mode enum, status transitions

#### **ConversationTurn Schemas** (`conversation_turn.py`)
- `ConversationTurnCreate`: Add new turn
- `ConversationTurnMessageRequest`: User input
- `ConversationTurnMessageResponse`: AI response + next action
- Validations: speaker and section enums, content not empty

#### **Document Schemas** (`document.py`)
- `DocumentCreate`: Initial document record
- `DocumentUploadResponse`: After upload
- `DocumentResponse`: Document info
- Validations: MIME type, max 25MB, filename

#### **ExtractedEntity Schemas** (`extracted_entity.py`)
- `ExtractedEntityCreate`: New extracted entity
- `ExtractedEntityResponse`: Entity info
- `LabAbnormalitySchema`: Lab result with abnormality status
- `detect_lab_abnormality()`: Deterministic function for lab abnormality
- Validations: entity_type enum, confidence 0-1, numeric value ranges

#### **Summary Schemas** (`summary.py`)
- `ClinicalSummaryContent`: Summary content structure
- `SummaryGenerateRequest`: Request to generate
- `SummaryPhysicianReviewRequest`: Physician review/approval
- `RedFlagAlert`: Red flag notification
- Validations: workflow_status enum, content not empty

#### **Consent Schemas** (`consent.py`)
- `ConsentCreate`: Create consent record
- `ConsentResponse`: Consent info
- `ConsentHistoryResponse`: Audit trail
- `ConsentRequest`: Request consent
- Validations: purpose enum, granted boolean, timestamps

#### **AuditLog Schemas** (`audit_log.py`)
- `AuditLogCreate`: Log new action
- `AuditLogResponse`: Log entry
- `AuditTrailReport`: Aggregated audit report
- `SensitiveActionLog`: Sensitive operation logging
- Validations: action and resource not empty, status enum

---

## Usage Patterns

### Create Resources
```python
# BAD: Don't use ORM models in requests
@router.post("/sessions/")
def create_session(session: Session):  # ❌ WRONG
    pass

# GOOD: Use Pydantic schemas
@router.post("/sessions/")
def create_session(session: SessionCreate):  # ✓ CORRECT
    db_session = Session(**session.dict())
    db.add(db_session)
    db.commit()
    return SessionResponse.from_orm(db_session)
```

### Response Serialization
```python
# Always use schemas for responses
@router.get("/sessions/{session_id}")
def get_session(session_id: uuid.UUID) -> SessionResponse:
    db_session = db.query(Session).filter(Session.id == session_id).first()
    return SessionResponse.from_orm(db_session)
```

### Validation
```python
# Pydantic validates automatically
@router.post("/patients/")
def create_patient(patient: PatientCreate):
    # If patient.dob is invalid ISO format:
    # Pydantic raises ValidationError automatically
    # FastAPI returns 422 with error details
    pass
```

---

## Relationships Summary

```
Patient (1)
  ├── Sessions (many) ────────────────────┐
  │    ├── ConversationTurns (many)       │
  │    ├── Documents (many)               │
  │    │    └── ExtractedEntities (many)  │
  │    ├── ExtractedEntities (many) ──────┤
  │    ├── Summaries (many)               │
  │    └── Consents (many) ───────────────┤
  │                                       │
  └── Consents (many) ────────────────────┘

AuditLog (standalone)
  └── References Session, User (but no FK)
```

---

## Database Migration

Run migrations with Alembic:

```bash
cd backend
alembic upgrade head
```

---

## Testing Models

See `backend/tests/test_models.py` for:
- Model instantiation tests
- Relationship tests
- Constraint tests
- Schema validation tests

---

## Key Design Principles

1. **Never expose ORM models to clients** - Always use Pydantic schemas
2. **Timestamps for everything** - Track when records created/updated
3. **Soft deletes for audit** - Consents never deleted, only revoked
4. **Lab abnormality is deterministic** - Hardcoded rules, not LLM
5. **Safety first** - Separate safety_status and safety_alerts fields
6. **Immutable audit logs** - Never update/delete audit records
7. **UUID for all PKs** - Better for distribution and privacy
8. **JSON for flexible data** - structured_history, metadata_json fields
9. **Indexes on foreign keys** - For query performance
10. **Explicit state machines** - Sections must be done in order

---

## Example: Complete Flow

```python
# 1. Patient registers
patient = PatientCreate(
    first_name="John",
    last_name="Doe",
    dob="1990-01-15",
    gender="MALE"
)
db_patient = Patient(**patient.dict())

# 2. Start session
session = SessionCreate(
    patient_id=db_patient.id,
    mode="MODERN"
)
db_session = Session(**session.dict())

# 3. First turn - Chief Complaint
turn1 = ConversationTurnCreate(
    session_id=db_session.id,
    speaker="PATIENT",
    section="CHIEF_COMPLAINT",
    content="I have been having headaches for 3 days"
)

# 4. Extract entity
entity = ExtractedEntityCreate(
    session_id=db_session.id,
    entity_type="SYMPTOM",
    entity_name="Headache",
    value="3 days duration",
    numeric_value=3.0,
    unit="days"
)

# 5. Consent for data sharing
consent = ConsentCreate(
    session_id=db_session.id,
    patient_id=db_patient.id,
    purpose="data_sharing",
    granted=True
)

# 6. Generate summary
summary = SummaryCreate(
    session_id=db_session.id
)
```

---

## References

- SQLAlchemy 2.0 Docs: https://docs.sqlalchemy.org/en/20/
- Pydantic v2 Docs: https://docs.pydantic.dev/latest/
- FHIR Standard: https://www.hl7.org/fhir/
- ABDM/ABHA: https://abdm.gov.in/
