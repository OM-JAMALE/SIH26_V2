# Health AI

A privacy-aware starter repository for healthcare conversations, document processing, summaries, consent, and integrations.

## Quick start

### Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Local development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

This scaffold contains mock-safe endpoints only. Configure production identity, storage, audit logging, and clinical safety review before handling real health data.
