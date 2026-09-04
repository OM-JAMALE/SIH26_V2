# API

The development API is exposed by FastAPI.

- `GET /health`: process health check
- `GET /api/v1/status`: API readiness status
- `POST /api/v1/conversation`: accepts `{ "message": "..." }` and returns a mock-safe response

Interactive OpenAPI documentation is available at `/docs` when the backend is running.
