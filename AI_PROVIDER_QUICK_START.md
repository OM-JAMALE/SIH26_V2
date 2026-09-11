# AI PROVIDER QUICK REFERENCE

## Installation & Setup

### Mock Provider (Default, No Setup)
```bash
# Works immediately, no external dependencies
python -c "from app.ai.providers import get_llm_provider; print(get_llm_provider())"
```

### OpenAI (Production)
```bash
# 1. Install
pip install openai

# 2. Set API key
export OPENAI_API_KEY=sk-your-key-here

# 3. Configure
export AI_PROVIDER=openai
```

### Ollama (Local)
```bash
# 1. Install Docker
# 2. Start server
docker run -d -p 11434:11434 ollama/ollama

# 3. Pull model
docker exec $(docker ps -q --filter ancestor=ollama/ollama) ollama pull qwen3

# 4. Configure
export AI_PROVIDER=local
export OLLAMA_MODEL=qwen3
```

---

## Basic Usage

### Get Provider
```python
from app.ai.providers import get_llm_provider

# Use configured provider
provider = get_llm_provider()

# Or specify explicitly
provider = get_llm_provider("openai")
provider = get_llm_provider("local")
provider = get_llm_provider("mock")
```

### Define Schema
```python
from pydantic import BaseModel

class Output(BaseModel):
    name: str
    age: int
    condition: str
```

### Generate Output
```python
result = provider.generate_structured(
    prompt="Patient: John, 45, chest pain",
    system_prompt="Extract patient info",
    schema_class=Output
)

print(result.name)  # "John"
print(result.age)   # 45
```

---

## Provider Comparison

| Provider | Setup | Cost | Speed | Best For |
|----------|-------|------|-------|----------|
| Mock | None | $0 | <1ms | Testing, CI/CD |
| OpenAI | API key | $$$ | Fast | Production |
| Local | Docker | $0 | Variable | Dev, On-prem |
| Gemini | API key | $$ | Fast | Alternative |

---

## Configuration

### .env File
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3
GEMINI_API_KEY=...
```

### Python
```python
from app.core.config import settings

settings.ai_provider = "openai"
settings.openai_api_key = "sk-..."
```

---

## Error Handling

```python
try:
    result = provider.generate_structured(...)
except ValueError as e:
    # Schema validation failed
    print(f"Invalid output: {e}")
except RuntimeError as e:
    # API error
    print(f"Provider error: {e}")
```

---

## Examples

### Extract Clinical Data
```python
from app.ai.providers import get_llm_provider
from app.ai.schemas.summary import ClinicalSummarySchema

provider = get_llm_provider()

summary = provider.generate_structured(
    prompt="Patient with chest pain and shortness of breath...",
    system_prompt="Extract clinical summary",
    schema_class=ClinicalSummarySchema
)
```

### Check Availability
```python
provider = get_llm_provider("openai")

if provider.is_available():
    result = provider.generate_structured(...)
else:
    # Fallback to mock
    provider = get_llm_provider("mock")
    result = provider.generate_structured(...)
```

### Service Integration
```python
from app.modules.documents.service import DocumentService

# Service uses configured provider automatically
service = DocumentService()

# Or specify provider
service = DocumentService(provider_type="openai")

# Use service (provider is transparent)
doc = await service.upload_and_process_document(...)
```

---

## Testing

### Run Provider Tests
```bash
cd backend
python -m pytest test_ai_providers.py -v
```

### Test Individual Provider
```python
from app.ai.providers import MockLLMProvider
from pydantic import BaseModel

class TestSchema(BaseModel):
    text: str

provider = MockLLMProvider()
result = provider.generate_structured(
    prompt="test",
    system_prompt="test",
    schema_class=TestSchema
)
assert result.text is not None
```

---

## Troubleshooting

### "API key not found"
```bash
export OPENAI_API_KEY=sk-...
# OR add to .env: OPENAI_API_KEY=sk-...
```

### "Connection refused" (Ollama)
```bash
# Check if running
docker ps | grep ollama

# Start if not running
docker run -d -p 11434:11434 ollama/ollama

# Verify
curl http://localhost:11434/api/tags
```

### "Schema validation failed"
```python
# Check provider is returning valid JSON
provider = get_llm_provider("mock")  # Use mock to debug
result = provider.generate_structured(...)

# Print result to verify structure
print(result.model_dump_json(indent=2))
```

---

## Environment Variables

| Variable | Options | Default |
|----------|---------|---------|
| AI_PROVIDER | mock, openai, gemini, local, ollama | mock |
| OPENAI_API_KEY | sk-... | (required for openai) |
| OPENAI_MODEL | gpt-4, gpt-4-turbo, etc. | gpt-4-turbo-preview |
| GEMINI_API_KEY | (key) | (optional) |
| OLLAMA_BASE_URL | http://... | http://localhost:11434 |
| OLLAMA_MODEL | qwen3, llama2, mistral | qwen3 |

---

## File Locations

```
backend/app/ai/providers/
├── base.py                 # Abstract base class
├── factory.py              # get_llm_provider() function
├── mock_provider.py        # MockLLMProvider
├── openai_provider.py      # OpenAIProvider
├── local_provider.py       # LocalLLMProvider (Ollama)
├── gemini_provider.py      # GeminiLLMProvider
└── __init__.py             # Public API

backend/test_ai_providers.py   # Comprehensive tests
AI_PROVIDER_ABSTRACTION_GUIDE.md  # Full documentation
```

---

## Quick Start Checklist

- [ ] Choose provider (mock for testing, openai for production)
- [ ] Install dependencies (pip install openai for OpenAI)
- [ ] Set environment variables (OPENAI_API_KEY, etc.)
- [ ] Import get_llm_provider
- [ ] Define Pydantic schema for output
- [ ] Call provider.generate_structured()
- [ ] Handle errors (ValueError, RuntimeError)

---

## Support

See full documentation: `AI_PROVIDER_ABSTRACTION_GUIDE.md`

Examples in test file: `backend/test_ai_providers.py`
