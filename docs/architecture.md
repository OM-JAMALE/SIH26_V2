# Architecture

Health AI is organized as a modular monolith.

- `app/api`: versioned HTTP transport and request validation
- `app/modules`: business capabilities such as conversation, documents, summaries, and consent
- `app/ai`: provider-neutral model adapters, prompts, and schemas
- `app/integrations`: external healthcare and language-system boundaries
- `app/db`: SQLAlchemy engine, models, and repositories
- `app/workers`: asynchronous jobs for long-running work

The frontend communicates with `/api/v1` and should never hold provider credentials.
