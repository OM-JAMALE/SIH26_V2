# Alembic Database Migrations - Health AI

## Status: ✓ COMPLETE AND TESTED

All database migrations have been successfully created and applied. The database schema is ready for production use.

---

## Migration Summary

### Migrations Applied

| # | Migration ID | Description | Status |
|---|---|---|---|
| 1 | `001_initial_schema` | Create 8 tables with foreign keys and indexes | ✓ Applied |
| 2 | `002_module_c_summary_update` | Add workflow fields to summaries table | ✓ Applied |
| 3 | `003_module_a_session_update` | Add safety and lifecycle fields to sessions | ✓ Applied |

**Current Database Version:** `003_module_a_session_update`

---

## Database Schema

### 1. **PATIENTS** (9 columns)
```
id: UUID [PK]
national_health_id: VARCHAR(100) [UNIQUE, INDEX]
first_name: VARCHAR(100) [NOT NULL]
last_name: VARCHAR(100) [NOT NULL]
dob: VARCHAR(20) [NOT NULL] - ISO format YYYY-MM-DD
gender: VARCHAR(20) [NOT NULL]
contact_number: VARCHAR(50) [NULLABLE]
created_at: DATETIME [NOT NULL, DEFAULT=NOW]
updated_at: DATETIME [NOT NULL, DEFAULT=NOW]
```

### 2. **SESSIONS** (15 columns)
```
id: UUID [PK]
patient_id: UUID [FK → patients, CASCADE]
status: VARCHAR(50) [NOT NULL] - INITIATED, IN_CONVERSATION, DOCUMENTS_UPLOADED, etc.
lifecycle_status: VARCHAR(50) [NOT NULL, DEFAULT='CREATED'] - CREATED, IN_PROGRESS, SAFETY_ESCALATED, COMPLETED
current_section: VARCHAR(50) [NOT NULL] - CHIEF_COMPLAINT, HPI, SOCRATES, etc.
mode: VARCHAR(20) [NOT NULL, DEFAULT='MODERN'] - MODERN or AYUSH
disclaimer_acknowledged: BOOLEAN [NOT NULL, DEFAULT=FALSE]
disclaimer_acknowledged_at: DATETIME [NULLABLE]
socrates_state: VARCHAR(50) [NULLABLE]
structured_history: JSON [NOT NULL, DEFAULT='{}']
safety_status: VARCHAR(50) [NOT NULL, DEFAULT='SAFE'] - SAFE, WARNING, ESCALATED
safety_alerts: JSON [NOT NULL, DEFAULT='{}']
session_metadata: JSON [NOT NULL, DEFAULT='{}']
created_at: DATETIME [NOT NULL, DEFAULT=NOW]
updated_at: DATETIME [NOT NULL, DEFAULT=NOW]

INDEXES:
- ix_sessions_status (status)
- ix_sessions_lifecycle_status (lifecycle_status)
```

### 3. **CONVERSATION_TURNS** (10 columns)
```
id: UUID [PK]
session_id: UUID [FK → sessions, CASCADE, INDEX]
turn_index: INTEGER [NOT NULL]
speaker: VARCHAR(20) [NOT NULL] - PATIENT or SYSTEM
content: TEXT [NOT NULL]
section: VARCHAR(50) [NOT NULL]
extracted_data: JSON [NOT NULL, DEFAULT='{}']
safety_alerts: JSON [NOT NULL, DEFAULT='{}']
created_at: DATETIME [NOT NULL, DEFAULT=NOW]
updated_at: DATETIME [NOT NULL, DEFAULT=NOW]

INDEXES:
- ix_conversation_turns_session_id (session_id)
```

### 4. **DOCUMENTS** (10 columns)
```
id: UUID [PK]
session_id: UUID [FK → sessions, CASCADE, INDEX]
filename: VARCHAR(255) [NOT NULL]
file_path: VARCHAR(500) [NOT NULL]
mime_type: VARCHAR(100) [NOT NULL] - application/pdf, image/png, image/jpeg
file_size: INTEGER [NOT NULL]
processing_status: VARCHAR(50) [NOT NULL] - PENDING, EXTRACTED, FAILED
raw_text: TEXT [NULLABLE]
created_at: DATETIME [NOT NULL, DEFAULT=NOW]
updated_at: DATETIME [NOT NULL, DEFAULT=NOW]

INDEXES:
- ix_documents_session_id (session_id)
```

### 5. **EXTRACTED_ENTITIES** (14 columns)
```
id: UUID [PK]
session_id: UUID [FK → sessions, CASCADE, INDEX]
document_id: UUID [FK → documents, CASCADE, INDEX, NULLABLE]
entity_type: VARCHAR(50) [NOT NULL] - LAB_RESULT, MEDICATION, DIAGNOSIS, VITAL, SYMPTOM
entity_name: VARCHAR(200) [NOT NULL]
value: VARCHAR(255) [NOT NULL]
numeric_value: FLOAT [NULLABLE]
unit: VARCHAR(50) [NULLABLE]
reference_range: VARCHAR(100) [NULLABLE]
is_abnormal: BOOLEAN [NOT NULL]
confidence_score: FLOAT [NOT NULL]
metadata_json: JSON [NOT NULL, DEFAULT='{}']
created_at: DATETIME [NOT NULL, DEFAULT=NOW]
updated_at: DATETIME [NOT NULL, DEFAULT=NOW]

INDEXES:
- ix_extracted_entities_session_id (session_id)
- ix_extracted_entities_document_id (document_id)
```

### 6. **SUMMARIES** (25 columns)
```
id: UUID [PK]
session_id: UUID [FK → sessions, CASCADE, INDEX]
version: INTEGER [NOT NULL]
workflow_status: VARCHAR(50) [NOT NULL] - NOT_GENERATED, GENERATING, GENERATED, PHYSICIAN_REVIEW, ACCEPTED, REJECTED
status: VARCHAR(50) [NOT NULL] - DRAFT, PUBLISHED (legacy)
chief_complaint: TEXT [NULLABLE]
hpi: TEXT [NULLABLE]
pmh: TEXT [NULLABLE]
drug_and_allergy: TEXT [NULLABLE]
family_history: TEXT [NULLABLE]
personal_history: TEXT [NULLABLE]
ros: TEXT [NULLABLE]
prior_investigations: TEXT [NULLABLE]
physician_notes: TEXT [NULLABLE]
llm_model: VARCHAR(100) [NOT NULL]
prompt_version: VARCHAR(50) [NOT NULL]
structured_summary: JSON [NULLABLE]
physician_edited_summary: JSON [NULLABLE]
generation_error: TEXT [NULLABLE]
accepted_at: DATETIME [NULLABLE]
accepted_by: VARCHAR(100) [NULLABLE]
rejected_at: DATETIME [NULLABLE]
rejected_reason: TEXT [NULLABLE]
created_at: DATETIME [NOT NULL, DEFAULT=NOW]
updated_at: DATETIME [NOT NULL, DEFAULT=NOW]

INDEXES:
- ix_summaries_session_id (session_id)
- ix_summaries_workflow_status (workflow_status)
```

### 7. **CONSENTS** (12 columns)
```
id: UUID [PK]
session_id: UUID [FK → sessions, CASCADE, INDEX]
patient_id: UUID [FK → patients, CASCADE, INDEX]
purpose: VARCHAR(255) [NOT NULL] - data_sharing, abdm_integration, fhir_export, research, quality_improvement
granted: BOOLEAN [NOT NULL]
terms_version: VARCHAR(50) [NOT NULL]
signature_hash: VARCHAR(255) [NULLABLE]
ip_address: VARCHAR(50) [NULLABLE]
granted_at: DATETIME [NULLABLE]
revoked_at: DATETIME [NULLABLE]
created_at: DATETIME [NOT NULL, DEFAULT=NOW]
updated_at: DATETIME [NOT NULL, DEFAULT=NOW]

INDEXES:
- ix_consents_session_id (session_id)
- ix_consents_patient_id (patient_id)
```

### 8. **AUDIT_LOGS** (10 columns)
```
id: UUID [PK]
session_id: UUID [FK → sessions, SET NULL, INDEX, NULLABLE]
user_id: VARCHAR(100) [NULLABLE]
action: VARCHAR(100) [NOT NULL]
resource: VARCHAR(100) [NOT NULL]
status: VARCHAR(50) [NOT NULL] - SUCCESS, FAILURE, FORBIDDEN
details: JSON [NOT NULL, DEFAULT='{}']
request_id: VARCHAR(100) [NULLABLE]
created_at: DATETIME [NOT NULL, DEFAULT=NOW]
updated_at: DATETIME [NOT NULL, DEFAULT=NOW]

INDEXES:
- ix_audit_logs_session_id (session_id)
```

---

## Relationships

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
  └── References Session (FK: SET NULL - audit log survives session deletion)
```

---

## Running Migrations

### Apply all migrations to head:
```bash
cd backend
alembic upgrade head
```

### Check current database version:
```bash
alembic current
```

### View migration history:
```bash
alembic history
```

### Create new migration (after model changes):
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply specific migration:
```bash
alembic upgrade 003_module_a_session_update
```

### Rollback last migration:
```bash
alembic downgrade -1
```

### Rollback all migrations:
```bash
alembic downgrade base
```

---

## Test Results

### Database Verification
```
Expected tables: 9
Actual tables: 9
- alembic_version (1 column)
- patients (9 columns)
- sessions (15 columns)
- conversation_turns (10 columns)
- documents (10 columns)
- extracted_entities (14 columns)
- summaries (25 columns)
- consents (12 columns)
- audit_logs (10 columns)

Indexes created: 12
- ix_audit_logs_session_id
- ix_consents_patient_id
- ix_consents_session_id
- ix_conversation_turns_session_id
- ix_documents_session_id
- ix_extracted_entities_document_id
- ix_extracted_entities_session_id
- ix_patients_national_health_id
- ix_sessions_lifecycle_status
- ix_sessions_status
- ix_summaries_session_id
- ix_summaries_workflow_status
```

### ORM Operations Test
```
[OK] Patient creation
[OK] Session creation
[OK] Conversation turn creation
[OK] Document creation
[OK] Extracted entity creation
[OK] Summary creation
[OK] Consent creation
[OK] Audit log creation
[OK] Relationships working
[OK] Cascade delete working
```

---

## Database Statistics

| Table | Columns | Indexes | Purpose |
|-------|---------|---------|---------|
| patients | 9 | 1 | Patient records |
| sessions | 15 | 2 | Consultation sessions |
| conversation_turns | 10 | 1 | Conversation messages |
| documents | 10 | 1 | Uploaded documents |
| extracted_entities | 14 | 2 | Extracted clinical data |
| summaries | 25 | 2 | Generated summaries |
| consents | 12 | 2 | Consent audit trail |
| audit_logs | 10 | 1 | System audit logs |

**Total:** 8 tables, 105 columns, 12 indexes

---

## Constraints & Cascade Rules

### Foreign Key Constraints

1. **sessions.patient_id → patients.id** (CASCADE)
   - When patient deleted, all sessions deleted

2. **conversation_turns.session_id → sessions.id** (CASCADE)
   - When session deleted, all turns deleted

3. **documents.session_id → sessions.id** (CASCADE)
   - When session deleted, all documents deleted

4. **extracted_entities.session_id → sessions.id** (CASCADE)
   - When session deleted, all entities deleted

5. **extracted_entities.document_id → documents.id** (CASCADE)
   - When document deleted, all its entities deleted

6. **summaries.session_id → sessions.id** (CASCADE)
   - When session deleted, all summaries deleted

7. **consents.session_id → sessions.id** (CASCADE)
   - When session deleted, consent records deleted

8. **consents.patient_id → patients.id** (CASCADE)
   - When patient deleted, consents deleted

9. **audit_logs.session_id → sessions.id** (SET NULL)
   - When session deleted, audit logs survive but FK set to NULL
   - Allows audit trail to persist after session deletion

---

## Migration Files

### 001_initial_schema.py
Creates 8 base tables: patients, sessions, conversation_turns, documents, extracted_entities, summaries, consents, audit_logs

**Migration ID:** `001_initial_schema`
**Revises:** None (base migration)
**Down Revises:** `002_module_c_summary_update`

### 002_module_c_summary_update.py
Adds workflow fields to summaries table:
- workflow_status (NOT_GENERATED, GENERATING, GENERATED, PHYSICIAN_REVIEW, ACCEPTED, REJECTED)
- structured_summary (JSON)
- physician_edited_summary (JSON)
- generation_error (Text)
- accepted_at, accepted_by (DateTime, String)
- rejected_at, rejected_reason (DateTime, Text)

**Migration ID:** `002_module_c_summary_update`
**Revises:** `001_initial_schema`
**Down Revises:** `003_module_a_session_update`

### 003_module_a_session_update.py
Adds safety and lifecycle fields to sessions table:
- lifecycle_status (CREATED, IN_PROGRESS, SAFETY_ESCALATED, COMPLETED)
- mode (MODERN or AYUSH)
- disclaimer_acknowledged, disclaimer_acknowledged_at
- socrates_state (SOCRATES sub-section)
- structured_history (JSON)
- safety_status (SAFE, WARNING, ESCALATED)
- safety_alerts (JSON)

**Migration ID:** `003_module_a_session_update`
**Revises:** `002_module_c_summary_update`
**Down Revises:** None (current head)

---

## Database Initialization

### First Time Setup
```bash
cd backend
alembic upgrade head
```

This will:
1. Create all 8 tables
2. Create all indexes
3. Create foreign key constraints
4. Set up cascade rules
5. Record migration history in alembic_version table

### Database URL (from .env or config)
**SQLite (Development):**
```
sqlite:///./health_ai.db
```

**PostgreSQL (Production):**
```
postgresql+psycopg://user:password@localhost:5432/health_ai
```

---

## Backup & Recovery

### Backup database before production:
```bash
# SQLite
cp health_ai.db health_ai_backup_$(date +%Y%m%d_%H%M%S).db

# PostgreSQL
pg_dump -U user health_ai > health_ai_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore database:
```bash
# SQLite
cp health_ai_backup_20240101_120000.db health_ai.db

# PostgreSQL
psql -U user health_ai < health_ai_backup_20240101_120000.sql
```

---

## Performance Optimization

### Query Performance Tips

1. **Always use indexed columns in WHERE clauses:**
   - session_id (most common)
   - patient_id (for patient lookups)
   - workflow_status (for summary filters)
   - lifecycle_status (for session filters)

2. **Example queries:**
   ```sql
   -- Fast: Uses index on session_id
   SELECT * FROM conversation_turns WHERE session_id = 'xxx' ORDER BY turn_index;
   
   -- Fast: Uses index on workflow_status
   SELECT * FROM summaries WHERE workflow_status = 'GENERATED';
   
   -- Fast: Uses index on patient_id
   SELECT * FROM consents WHERE patient_id = 'xxx';
   ```

3. **Avoid full table scans:**
   ```sql
   -- Slow: No index on content
   SELECT * FROM conversation_turns WHERE content LIKE '%headache%';
   
   -- Consider: Pre-extract and index key words via extracted_entities
   SELECT ct.* FROM conversation_turns ct 
   JOIN extracted_entities ee ON ct.session_id = ee.session_id
   WHERE ee.entity_name = 'Headache';
   ```

---

## Monitoring

### Check database size:
```bash
# SQLite
ls -lh health_ai.db

# PostgreSQL
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size 
FROM pg_database WHERE datname = 'health_ai';
```

### Count records:
```sql
SELECT 'patients' as table_name, COUNT(*) FROM patients
UNION ALL
SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL
SELECT 'conversation_turns', COUNT(*) FROM conversation_turns
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'extracted_entities', COUNT(*) FROM extracted_entities
UNION ALL
SELECT 'summaries', COUNT(*) FROM summaries
UNION ALL
SELECT 'consents', COUNT(*) FROM consents
UNION ALL
SELECT 'audit_logs', COUNT(*) FROM audit_logs;
```

---

## Verification Commands

All tests completed successfully:

```bash
# Verify migrations applied
cd backend
alembic current
# Output: 003_module_a_session_update (head)

# Verify database
python verify_db.py
# Output: SUCCESS: ALL TABLES AND INDEXES CREATED

# Verify ORM operations
python test_orm_db.py
# Output: SUCCESS: ALL ORM OPERATIONS WORKING
```

---

## Production Checklist

- [x] All migrations created and tested
- [x] All 8 tables created with correct columns
- [x] All 12 indexes created
- [x] All foreign keys with correct cascade rules
- [x] UUID primary keys on all tables
- [x] Timestamps (created_at, updated_at) on all tables
- [x] JSON fields for flexible data
- [x] ORM relationships working
- [x] Cascade delete working
- [x] Database verified and tested

**Status: READY FOR PRODUCTION**

---

## References

- Alembic Documentation: https://alembic.sqlalchemy.org/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Migration files: `backend/alembic/versions/`
- Verification scripts: `backend/verify_db.py`, `backend/test_orm_db.py`
