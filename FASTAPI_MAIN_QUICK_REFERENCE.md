# FASTAPI MAIN.PY QUICK REFERENCE

## CORS Configuration

### Development
```bash
# .env
APP_ENV=development
CORS_ORIGINS=["http://localhost:5173"]
```

Automatically allows:
- http://localhost:5173 (React Vite)
- http://127.0.0.1:5173
- http://localhost:3000
- http://localhost:8000

### Production
```bash
# .env
APP_ENV=production
CORS_ORIGINS=["https://app.example.com","https://www.example.com"]
```

Uses strict whitelist only

---

## Error Handling

### Validation Errors (422)
```json
{
  "error": "Validation error",
  "code": "VALIDATION_ERROR",
  "status": 422,
  "errors": [
    {"field": "patient_id", "message": "invalid UUID"}
  ],
  "request_id": "req-123"
}
```

### Server Errors (500)
```json
{
  "error": "Internal server error",
  "code": "INTERNAL_SERVER_ERROR",
  "status": 500,
  "request_id": "req-123"
}
```

---

## Logging

### What's Logged
- ✓ Method (GET, POST, etc.)
- ✓ Path (/api/v1/sessions/, etc.)
- ✓ Status code (200, 404, 500, etc.)
- ✓ Response time (milliseconds)
- ✓ Request ID (tracing)

### What's NOT Logged
- ✗ Request body
- ✗ Response body
- ✗ Patient data
- ✗ Clinical information

### Example Log Output
```
[req-abc-123] → POST /api/v1/sessions/
[req-abc-123] ✓ POST /api/v1/sessions/ - 201 (0.245s)

[req-def-456] → GET /api/v1/sessions/invalid-id
[req-def-456] ✗ GET /api/v1/sessions/invalid-id - 404 (0.012s)
```

---

## Health Check Endpoint

### Request
```bash
GET /health
```

### Success Response (200)
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok"
}
```

### Degraded Response (503)
```json
{
  "status": "degraded",
  "database": "ok",
  "redis": "error",
  "errors": ["Redis: Connection refused"]
}
```

### Usage Examples

**Monitoring:**
```bash
curl http://localhost:8000/health | jq .status
```

**Kubernetes Liveness:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
```

**Load Balancer:**
```
GET /health → 200 = healthy
GET /health → 503 = unhealthy
```

---

## Middleware Stack

1. **RequestIDMiddleware** — Add unique ID
2. **RequestLoggingMiddleware** — Log method/path/status/time
3. **CORSMiddleware** — Handle CORS
4. [Route Handler]
5. [Response]

---

## Startup Logs

```
✓ Database tables created
✓ Database connection verified
✓ Redis connection verified
✓ CORS configured
✓ Middleware configured
✓ Error handlers registered
✓ Health check endpoint registered
✓ API v1 router mounted
```

---

## Configuration Examples

### Development (.env)
```
APP_ENV=development
DATABASE_URL=sqlite:///./health_ai.db
REDIS_URL=redis://localhost:6379/0
AI_PROVIDER=mock
```

### Production (.env)
```
APP_ENV=production
DATABASE_URL=postgresql://user:pass@prod-db:5432/health_ai
REDIS_URL=redis://prod-redis:6379/0
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
CORS_ORIGINS=["https://app.example.com"]
```

---

## Testing

### Test Health Check
```bash
curl http://localhost:8000/health
```

### Test CORS
```bash
curl -H "Origin: http://localhost:5173" \
  -X OPTIONS http://localhost:8000/api/v1/sessions/
```

### Test Error Handling
```bash
# Validation error
curl -X POST http://localhost:8000/api/v1/sessions/ \
  -H "Content-Type: application/json" \
  -d '{}'
# Response: 422 VALIDATION_ERROR
```

---

## Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## Key Features

✓ Environment-aware CORS
✓ Global error handlers
✓ Request/response logging (no PII)
✓ Health checks (DB + Redis)
✓ Request ID tracing
✓ Proper lifecycle management
✓ Auto documentation
✓ Production-ready

---

## File

`backend/app/main.py` (12.7 KB)
- 400+ lines
- Fully documented
- Production-grade
