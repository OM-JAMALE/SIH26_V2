# Healthcare AI Platform - AI & Developer Onboarding Guide

> **IMPORTANT**: Any AI assistant or software engineer taking over this repository MUST read and adhere strictly to the guidelines documented in this file before proposing or executing code changes.

---

## 📌 1. Core Architectural Principle

### **THE LLM IS NOT THE SOURCE OF TRUTH**

In this platform:
- **LLM Responsibilities**:
  - Formulates natural language follow-up queries.
  - Interprets informal, non-conventional, or noisy patient text.
  - Extracts key-value entities from documents and chat turns.
  - Drafts structured clinical summary text.

- **Deterministic Application Code Responsibilities**:
  - **State Machine Transitions**: Section progression (`CHIEF_COMPLAINT` → `SOCRATES` → `PMH` → `COMPLETED`) is strictly governed by Python state machines (`app/modules/conversation/state_machine.py`).
  - **Emergency Safety Triage**: Red-flag symptom checks evaluate against inspectable regex/keyword rules (`app/modules/conversation/service.py`). An LLM can NEVER override an emergency alert.
  - **Numerical Lab Range Analysis**: Laboratory range abnormalities are computed via quantitative threshold comparisons (`app/modules/documents/service.py`).
  - **Data Validation & Persistence**: Pydantic v2 schemas and SQLAlchemy 2.0 handle data contracts and transaction safety.
  - **Permissions & Consent**: Access control and explicit patient consent tracking are governed deterministically (`app/integrations/consent_manager.py`).

---

## 📁 2. Codebase Structure & Key Files

```
SIH26_V2/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── providers/          # AI Provider Abstractions (base, mock, openai, local)
│   │   │   ├── prompts/            # Clinical & Summary Generation Prompts
│   │   │   └── factory.py          # AI Provider Factory (get_llm_provider)
│   │   ├── core/
│   │   │   ├── config.py           # System settings & environment variables
│   │   │   ├── audit.py            # Privacy-preserving audit logging (Redacts patient text & tokens)
│   │   │   ├── logging.py          # Structured JSON logger
│   │   │   └── middleware.py       # Request correlation ID & tracing
│   │   ├── db/
│   │   │   ├── models/             # SQLAlchemy ORM models (patient, session, conversation_turn, etc.)
│   │   │   └── session.py          # Database session engine
│   │   ├── integrations/
│   │   │   ├── fhir_adapter.py     # HL7 FHIR R4 DiagnosticReport & Observation adapters
│   │   │   ├── abdm_adapter.py     # Ayushman Bharat Digital Mission (ABDM) HIP payload bundle
│   │   │   └── consent_manager.py  # Patient consent grant/revocation log
│   │   ├── modules/
│   │   │   ├── conversation/       # Module A: Conversational history engine & state machine
│   │   │   ├── documents/          # Module B: Medical document digitization & lab extraction
│   │   │   └── summary/            # Module C: Clinical summary generator & physician review
│   │   └── main.py                 # FastAPI application entrypoint
│   └── tests/                      # Pytest suite (60+ unit & integration tests)
├── frontend/
│   ├── src/
│   │   ├── api/                    # Typed HTTP client wrappers (Axios / Fetch)
│   │   ├── components/             # UI Components (Sidebar, Skeletons, Toast, ErrorBoundary)
│   │   ├── pages/                  # Views (Identify, Conversation, Documents, Summary, Consent)
│   │   └── App.tsx                 # Layout & workflow navigation controller
│   └── src/tests/                  # Vitest integration tests
├── docs/                           # Architecture, Deployment, API, & Production Readiness docs
├── NEXT_PHASES_ROADMAP.txt         # Granular sub-phase roadmap
├── docker-compose.yml              # Production stack (Frontend, Backend, Postgres, Redis)
└── README.md                       # Main setup & quickstart guide
```

---

## 🔒 3. Non-Negotiable Development Rules

1. **Never Put Business Logic in Route Handlers**:
   - Strictly follow: `API Route Handler` → `Service Layer` → `Repository / ORM` → `Database`.
2. **Privacy Audit Logging**:
   - Audit logs (`AuditLog`) MUST NEVER contain raw patient clinical narratives, LLM response texts, or secret API credentials. Always use `log_audit_event()` from `app.core.audit`.
3. **Preserve Test Integrity**:
   - Never comment out failing tests or swallow exceptions silently.
   - Always run `pytest tests/` in `backend` and `npx vitest run` in `frontend` after making modifications.
4. **Offline Mock Fallback**:
   - The platform MUST be able to run offline using `AI_PROVIDER=mock` when no external API key is configured.
5. **Incremental Sub-Phase Execution**:
   - Work must be executed strictly **one sub-phase at a time** (Sub-Phases A.1 through B.3) to avoid exceeding context or tool limits.

---

## 🚀 4. Sub-Phase Execution Roadmap

### Phase A: End-to-End English Real AI Core + Portals + Glassmorphic UI
- **Sub-Phase A.1**: Real AI Engine & English Non-Conventional Input Adaptation (`factory.py`, `openai_provider.py`, Pydantic validation).
- **Sub-Phase A.2**: Patient Past Session History & Doctor Search APIs (`GET /api/v1/patients/{patient_id}/sessions`, `GET /api/v1/doctors/patients/search`).
- **Sub-Phase A.3**: Glassmorphic UI Design System & App Navigation Layout (`index.css`, `App.css`, `App.tsx`).
- **Sub-Phase A.4**: Patient Dashboard Portal (`PatientDashboardPage.tsx`).
- **Sub-Phase A.5**: Doctor Portal & Summary Sign-off (`DoctorDashboardPage.tsx`).

### Phase B: Regional Language Expansion & Multilingual Voice Intake
- **Sub-Phase B.1**: Speech-to-Text & Text-to-Speech Hooks (`useVoiceInput.ts`, `useTextToSpeech.ts`).
- **Sub-Phase B.2**: Multilingual Voice Chat UI Integration (`ConversationPage.tsx`).
- **Sub-Phase B.3**: Multilingual Translation & Clinical Standardization Pipeline (`summary_service.py`).

---

## 🧪 5. Testing & Verification Commands

```bash
# Run Backend Tests
cd backend
python -m pytest tests/

# Run Frontend Build Verification
cd frontend
npm run build

# Run Frontend Integration Tests
cd frontend
npx vitest run
```
