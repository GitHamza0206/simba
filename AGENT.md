# AGENT.md - Simba Development Guidelines

## Project Overview

**Simba** is an open-source Customer Service Assistant as a Service platform. It provides embeddable AI-powered customer support that answers questions fast and accurately.

> **Important**: This is a rewrite of an existing repository. The codebase is being modernized with a new architecture while preserving the core "Simba" branding.

---

## Architecture Summary

### Frontend Stack
- **Framework**: Next.js 16+ (App Router)
- **Language**: TypeScript (strict mode)
- **State Management**: TanStack Query (React Query)
- **UI Components**: shadcn/ui + Radix UI primitives
- **Styling**: Tailwind CSS
- **API Layer**: tRPC (optional) or REST
- **Package Manager**: pnpm
- **Final Deliverable**: npm package for embedding (`@simba/widget`)

### Backend Stack
- **Framework**: FastAPI (Python 3.11+)
- **Package Manager**: uv
- **Database**: PostgreSQL (primary), SQLite (development)
- **Vector Store**: pgvector (PostgreSQL extension), FAISS (local)
- **Task Queue**: Celery + Redis
- **ORM**: SQLAlchemy 2.0

---

## Code Standards

### TypeScript/Frontend

```typescript
// Naming conventions
- Components: PascalCase (e.g., ChatWidget.tsx)
- Hooks: camelCase with 'use' prefix (e.g., useChat.ts)
- Utils: camelCase (e.g., formatMessage.ts)
- Types: PascalCase with descriptive suffixes (e.g., ChatMessageType, ApiResponse)
- Constants: SCREAMING_SNAKE_CASE

// File structure for components
src/
  components/
    chat/
      ChatWidget.tsx        # Main component
      ChatMessage.tsx       # Sub-components
      chat.types.ts         # Local types
      useChat.ts            # Component-specific hook
      index.ts              # Barrel export
```

### Python/Backend

```python
# Naming conventions
- Modules: snake_case (e.g., document_service.py)
- Classes: PascalCase (e.g., DocumentService)
- Functions: snake_case (e.g., process_document)
- Constants: SCREAMING_SNAKE_CASE
- Private methods: _leading_underscore

# File structure
simba/
  api/
    routes/           # FastAPI routers
    schemas/          # Pydantic models
  core/
    config.py         # Configuration
    security.py       # Auth utilities
  services/           # Business logic
  models/             # SQLAlchemy models
  repositories/       # Data access layer
```

---

## Critical Guidelines

### DO

1. **Write tests first** for critical paths (evals are mandatory for AI responses)
2. **Use type hints everywhere** - both TypeScript strict mode and Python type annotations
3. **Follow the existing patterns** - check similar files before creating new ones
4. **Keep components small** - single responsibility, < 200 lines preferred
5. **Document public APIs** - JSDoc for TS, docstrings for Python
6. **Use environment variables** for configuration - never hardcode secrets
7. **Implement proper error handling** - use custom error classes
8. **Write semantic commit messages** following Conventional Commits

### DON'T

1. **Don't skip evaluations** - AI response quality must be measured
2. **Don't ignore TypeScript errors** - fix them, don't use `@ts-ignore`
3. **Don't mix business logic with UI** - use hooks/services layer
4. **Don't create God components** - split into smaller pieces
5. **Don't commit `.env` files** - use `.env.example` as template
6. **Don't add dependencies without justification** - keep bundle size small
7. **Don't write raw SQL** - use SQLAlchemy ORM or query builders
8. **Don't bypass the PR process** - all changes need review

---

## API Design Principles

### REST Endpoints

```
GET    /api/v1/conversations          # List conversations
POST   /api/v1/conversations          # Create conversation
GET    /api/v1/conversations/{id}     # Get conversation
DELETE /api/v1/conversations/{id}     # Delete conversation

POST   /api/v1/conversations/{id}/messages   # Send message
GET    /api/v1/conversations/{id}/messages   # Get messages

POST   /api/v1/documents              # Upload document
GET    /api/v1/documents/{id}/chunks  # Get document chunks

POST   /api/v1/retrieval/search       # Semantic search
```

### Response Format

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "uuid"
  }
}

// Error response
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

---

## Evaluation Requirements (CRITICAL)

The backend **MUST** have strong evaluations. Every AI-powered feature needs:

### Response Quality Evals
- **Relevance Score**: Does the response answer the question?
- **Accuracy Score**: Is the information factually correct?
- **Completeness Score**: Does it fully address the query?
- **Citation Score**: Are sources properly referenced?

### Performance Evals
- **Latency**: p50, p95, p99 response times
- **Retrieval Quality**: MRR, NDCG for search results
- **Hallucination Rate**: Track and minimize fabricated info

### Implementation
```python
# Every AI endpoint should log eval metrics
@router.post("/chat")
async def chat(request: ChatRequest):
    response = await generate_response(request)

    # Log evaluation metrics
    await log_eval_metrics(
        request_id=request.id,
        relevance=calculate_relevance(request.query, response),
        latency_ms=response.latency,
        retrieval_scores=response.retrieval_metrics
    )

    return response
```

---

## Embedding Widget Specifications

The final npm package (`@simba/widget`) must be:

### Easy to Integrate
```html
<!-- Script tag integration -->
<script src="https://cdn.simba.ai/widget.js"></script>
<script>
  Simba.init({
    apiKey: 'your-api-key',
    theme: 'light',
    position: 'bottom-right'
  });
</script>
```

```tsx
// React integration
import { SimbaWidget } from '@simba/widget';

<SimbaWidget
  apiKey="your-api-key"
  theme="light"
  onMessage={(msg) => console.log(msg)}
/>
```

### Customizable
- Theming (colors, fonts, spacing)
- Position (corners, inline)
- Behavior (auto-open, triggers)
- Branding (logo, name)

### Lightweight
- Target: < 50KB gzipped
- Lazy loading for heavy features
- Tree-shakeable exports

---

## Git Workflow

### Branch Naming
```
feature/   - New features (feature/chat-widget)
fix/       - Bug fixes (fix/message-scroll)
refactor/  - Code improvements (refactor/api-layer)
docs/      - Documentation (docs/api-reference)
test/      - Test additions (test/eval-suite)
```

### Commit Messages
```
feat: add chat widget component
fix: resolve message ordering issue
docs: update API documentation
test: add evaluation test suite
refactor: extract message formatting logic
chore: update dependencies
```

---

## Environment Setup

### Required Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/simba
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=sk-...
VECTOR_STORE_TYPE=pgvector

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Development Commands
```bash
# Backend
uv sync                    # Install dependencies
uv run simba server        # Start API server
uv run pytest              # Run tests

# Frontend
pnpm install               # Install dependencies
pnpm dev                   # Start dev server
pnpm test                  # Run tests
pnpm build                 # Production build
```

---

## Security Checklist

- [ ] Input validation on all endpoints
- [ ] Rate limiting implemented
- [ ] API key authentication
- [ ] CORS properly configured
- [ ] SQL injection prevention (use ORM)
- [ ] XSS prevention (sanitize outputs)
- [ ] Secrets in environment variables only
- [ ] Audit logging for sensitive operations

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Chat response (p95) | < 2s |
| Document upload | < 5s for 10MB |
| Search latency (p95) | < 500ms |
| Widget load time | < 1s |
| Time to first message | < 100ms |

---

## Questions?

Before making significant architectural decisions, consult the team. When in doubt:
1. Check existing patterns in the codebase
2. Reference this document
3. Ask in the PR discussion
