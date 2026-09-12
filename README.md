# Healthcare AI Pre-Consultation & Clinical History Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![HL7 FHIR](https://img.shields.io/badge/HL7%20FHIR-R4-orange.svg)](https://hl7.org/fhir/)

A privacy-preserving, auditable, pre-consultation clinical history taking and document digitization platform.

---

## 🌟 Executive Overview

The Healthcare AI Platform streamlines pre-consultation intake for physicians and clinic workflows. It collects structured history using adaptive clinical section transitions (SOCRATES framework), digitizes laboratory reports, flags numerical abnormalities and red-flag emergency symptoms deterministically, generates verified clinical summaries for physician review, and exports compliant HL7 FHIR R4 and ABDM bundles.

---

## 🛡️ Critical Architectural Principle

> **The LLM is NOT the source of truth.**

1. **LLM Responsibilities**:
   - Interprets natural language patient text.
   - Formulates empathetic, context-aware conversational questions.
   - Extracts structured key-value entities from patient text and OCR documents.
   - Drafts preliminary clinical summary text.

2. **Deterministic Python Code Responsibilities**:
   - **State Machine Transitions**: Section progression (CHIEF_COMPLAINT → SOCRATES → PMH → COMPLETED) is strictly enforced by Python state machines.
   - **Emergency Safety Triage**: Red-flag symptom checks evaluate against inspectable regex/keyword rules. An LLM cannot override an emergency trigger.
   - **Numerical Lab Range Analysis**: Laboratory range abnormalities are computed via numerical threshold comparisons.
   - **Data Validation & Persistence**: Pydantic v2 and SQLAlchemy 2.0 handle schema enforcement and database transaction bounds.
   - **Permissions & Consent**: Access control and explicit patient consent tracking are governed deterministically.

---

## 🏗️ Repository Architecture

```
SIH26_V2/
├── backend/                  # FastAPI Modular Monolith Service
│   ├── app/
│   │   ├── ai/               # AI Provider Abstraction (Mock, OpenAI, Local) & Prompts
│   │   ├── core/             # Configuration, Privacy Audit Logging, Middleware
│   │   ├── db/               # SQLAlchemy Models, Database Session, Alembic Migrations
│   │   ├── integrations/     # FHIR R4, ABDM (ABHA), Consent Tracking Adapters
│   │   ├── modules/
│   │   │   ├── conversation/ # Module A: State machine & turn persistence
│   │   │   ├── documents/    # Module B: Digitization & lab range extraction
│   │   │   └── summary/      # Module C: Clinical summary & physician review workflow
│   │   └── main.py           # FastAPI application entrypoint
│   ├── tests/                # Automated Pytest suite (60+ unit & integration tests)
│   └── Dockerfile
├── frontend/                 # Vite + React Client
│   ├── src/
│   │   ├── api/              # Typed Axios HTTP client wrappers
│   │   ├── components/       # UI Components (Sidebar, Header, Skeleton, Toast, ErrorBoundary)
│   │   ├── pages/            # Conversation, Documents, Summary, Consent views
│   │   └── App.tsx           # Navigation & Layout Controller
│   └── package.json
├── docs/                     # System Architecture, Deployment & API Reference
│   ├── api.md                # Complete REST API reference
│   ├── deployment.md         # Production Docker Compose guide
│   └── models_and_schemas.md # Database schema documentation
├── docker-compose.yml        # Orchestration (Frontend, Backend, Postgres, Redis)
└── README.md
```

---

## 🚀 Quickstart Guide

### Option 1: Development Stack (Local Server)

#### Backend Setup:
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
- Open Frontend: `http://localhost:5173`
- Swagger Interactive API Docs: `http://localhost:8000/docs`

---

### Option 2: Production Stack (Docker Compose)

Launch the full container stack (Frontend, Backend, PostgreSQL 16, Redis 7):

```bash
docker compose up -d --build
```

- **Frontend UI**: `http://localhost:5173`
- **Backend REST API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`

---

## 📦 Core Feature Modules

### Module A: Conversational History Engine
- Deterministic section state machine (`CHIEF_COMPLAINT` → `SOCRATES` → `PMH` → `COMPLETED`).
- Full conversation turn persistence for restart resilience.
- Real-time emergency red-flag triage with instant referral warning banners.

### Module B: Medical Document Digitization
- Multi-format ingestion (PDF, PNG, JPEG, max 10MB).
- Deterministic numerical abnormality classification for lab parameters.

### Module C: Structured Clinical Summary Generator
- Bounded LLM summary generation with Pydantic schema validation.
- Physician review workflow (`DRAFT` → `PHYSICIAN_REVIEW` → `ACCEPTED` / `REJECTED`).
- Complete separation between raw AI output and physician edits.

### Module D: Consent, Privacy & Healthcare Integrations
- Explicit patient consent logging (`log_consent_action`).
- **Privacy Audit Logger**: Redacts clinical narratives and secret tokens before DB write (`[REDACTED_CLINICAL_CONTENT]`).
- **HL7 FHIR R4 Adapter**: Generates `DiagnosticReport` and `Observation` resources.
- **ABDM Adapter**: Produces ABHA-linked HIP document bundles with fallback error handling.

---

## 🧪 Testing

### Backend Unit & Integration Tests (Pytest):
```bash
cd backend
pytest tests/
```

### Frontend Integration Tests (Vitest):
```bash
cd frontend
npm run test
```

---

## 🔒 Security & Healthcare Safety

- **No Secret Leaks**: All secrets configured via environment variables.
- **Privacy Logging**: Patient clinical text is never logged to system stdout or audit logs.
- **CORS Hardening**: Explicit origin whitelisting configured in `app/core/config.py`.
- **Medical Disclaimer**: System explicitly states it does not diagnose patients. Emergency alerts require immediate professional evaluation.
