# Decisions

## Modular monolith first

The initial system keeps domain modules in one deployable FastAPI service. This reduces operational overhead while preserving boundaries for later extraction.

## Provider-neutral AI boundary

AI providers are isolated under `app/ai/providers` so model selection and vendor credentials do not leak into domain code.

## Mock-first development

The default conversation endpoint is deterministic and does not call an external model. Production providers should be added only with explicit safety, privacy, and evaluation controls.
