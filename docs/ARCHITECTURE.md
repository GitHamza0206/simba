# Simba Technical Architecture

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CLIENT SIDE                                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │   Simba Widget  │    │  Dashboard App  │    │   Third-Party   │      │
│  │   (npm package) │    │    (Next.js)    │    │   Integrations  │      │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘      │
│           │                      │                      │                │
└───────────┼──────────────────────┼──────────────────────┼────────────────┘
            │                      │                      │
            └──────────────────────┼──────────────────────┘
                                   │
                         ┌─────────▼─────────┐
                         │   API Gateway     │
                         │   (REST/tRPC)     │
                         └─────────┬─────────┘
                                   │
┌──────────────────────────────────┼───────────────────────────────────────┐
│                              SERVER SIDE                                  │
├──────────────────────────────────┼───────────────────────────────────────┤
│                                  │                                        │
│              ┌───────────────────▼───────────────────┐                   │
│              │           FastAPI Server              │                   │
│              │                                       │                   │
│              │  ┌─────────┐ ┌─────────┐ ┌─────────┐ │                   │
│              │  │  Chat   │ │Documents│ │Retrieval│ │                   │
│              │  │ Routes  │ │ Routes  │ │ Routes  │ │                   │
│              │  └────┬────┘ └────┬────┘ └────┬────┘ │                   │
│              │       │          │           │       │                   │
│              │  ┌────▼──────────▼───────────▼────┐  │                   │
│              │  │         Service Layer          │  │                   │
│              │  │  ┌──────┐ ┌──────┐ ┌────────┐  │  │                   │
│              │  │  │ Chat │ │ Doc  │ │Retrieval│  │  │                   │
│              │  │  └──┬───┘ └──┬───┘ └───┬────┘  │  │                   │
│              │  └─────┼────────┼─────────┼───────┘  │                   │
│              └────────┼────────┼─────────┼──────────┘                   │
│                       │        │         │                               │
│  ┌────────────────────┼────────┼─────────┼────────────────────────────┐ │
│  │                    │        │         │                             │ │
│  │  ┌─────────────────▼────────▼─────────▼──────────────────────────┐ │ │
│  │  │                    Repository Layer                            │ │ │
│  │  └─────────────────┬────────┬─────────┬──────────────────────────┘ │ │
│  │                    │        │         │                             │ │
│  │    ┌───────────────▼──┐ ┌───▼───┐ ┌───▼───────────┐                │ │
│  │    │   PostgreSQL     │ │ Redis │ │  Vector Store │                │ │
│  │    │   (Primary DB)   │ │(Cache)│ │   (pgvector)  │                │ │
│  │    └──────────────────┘ └───────┘ └───────────────┘                │ │
│  │                                                                     │ │
│  │                         DATA LAYER                                  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                      BACKGROUND WORKERS                              │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐    │ │
│  │  │  Document  │  │  Embedding │  │    Eval    │  │   Cleanup  │    │ │
│  │  │  Parser    │  │  Generator │  │   Runner   │  │   Worker   │    │ │
│  │  └────────────┘  └────────────┘  └────────────┘  └────────────┘    │ │
│  │                           │                                         │ │
│  │                    ┌──────▼──────┐                                  │ │
│  │                    │   Celery    │                                  │ │
│  │                    │   + Redis   │                                  │ │
│  │                    └─────────────┘                                  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 16+ (App Router) | Server components, routing, SSR |
| Language | TypeScript (strict) | Type safety, better DX |
| State | TanStack Query v5 | Server state, caching |
| UI Library | shadcn/ui | Pre-built accessible components |
| Primitives | Radix UI | Headless component primitives |
| Styling | Tailwind CSS v4 | Utility-first CSS |
| API Client | tRPC (optional) | End-to-end type safety |
| Package Manager | pnpm | Fast, disk-efficient |
| Build | Vite (for widget) | Fast bundling for npm package |

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | Async Python web framework |
| Language | Python 3.11+ | Type hints, performance |
| Package Manager | uv | Fast Python package manager |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Validation | Pydantic v2 | Data validation, serialization |
| Task Queue | Celery | Background job processing |
| Cache/Broker | Redis | Caching, task queue broker |

### Data Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| Primary DB | PostgreSQL 15+ | Relational data storage |
| Vector Store | pgvector | Vector similarity search |
| Alternative VS | FAISS | Local development, air-gapped |
| Object Storage | MinIO/S3 | Document file storage |
| Search | PostgreSQL FTS | Keyword search fallback |

### AI/ML

| Component | Technology | Purpose |
|-----------|------------|---------|
| LLM | OpenAI/Anthropic/Ollama | Response generation |
| Embeddings | HuggingFace/OpenAI | Text vectorization |
| Framework | LangChain | LLM orchestration |
| Evaluation | Custom + LangSmith | Quality measurement |

---

## Directory Structure

### Root

```
simba/
├── AGENT.md                 # AI assistant guidelines
├── README.md                # Project overview
├── LICENSE.md               # License information
├── Makefile                 # Common commands
├── pyproject.toml           # Python project config
├── docker/                  # Docker configurations
├── docs/                    # Documentation
│   ├── VISION.md
│   ├── ARCHITECTURE.md
│   └── UI_UX_GUIDELINES.md
├── simba/                   # Backend (Python/FastAPI)
├── frontend/                # Dashboard (Next.js)
├── packages/                # Frontend packages
│   └── widget/              # Embeddable widget (npm)
└── simba_sdk/               # Python SDK
```

### Backend Structure

```
simba/
├── __init__.py
├── __main__.py              # Entry point
├── cli.py                   # CLI commands
├── config.py                # Configuration management
│
├── api/                     # API layer
│   ├── __init__.py
│   ├── app.py               # FastAPI application
│   ├── deps.py              # Dependencies (DI)
│   ├── middleware/          # Custom middleware
│   │   ├── auth.py
│   │   ├── cors.py
│   │   └── logging.py
│   ├── routes/              # Route handlers
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── documents.py
│   │   ├── retrieval.py
│   │   ├── conversations.py
│   │   └── health.py
│   └── schemas/             # Pydantic models (API)
│       ├── __init__.py
│       ├── chat.py
│       ├── document.py
│       └── common.py
│
├── core/                    # Core utilities
│   ├── __init__.py
│   ├── config.py            # Settings management
│   ├── security.py          # Auth utilities
│   ├── exceptions.py        # Custom exceptions
│   └── logging.py           # Logging setup
│
├── models/                  # SQLAlchemy models
│   ├── __init__.py
│   ├── base.py              # Base model class
│   ├── document.py
│   ├── conversation.py
│   ├── message.py
│   └── chunk.py
│
├── repositories/            # Data access layer
│   ├── __init__.py
│   ├── base.py              # Base repository
│   ├── document.py
│   ├── conversation.py
│   └── vector.py
│
├── services/                # Business logic
│   ├── __init__.py
│   ├── chat.py              # Chat orchestration
│   ├── document.py          # Document processing
│   ├── retrieval.py         # Search & retrieval
│   ├── embedding.py         # Vector generation
│   └── llm.py               # LLM interactions
│
├── workers/                 # Celery tasks
│   ├── __init__.py
│   ├── celery.py            # Celery app
│   ├── document.py          # Document tasks
│   └── eval.py              # Evaluation tasks
│
└── evals/                   # Evaluation framework
    ├── __init__.py
    ├── metrics.py           # Metric definitions
    ├── runners.py           # Eval execution
    └── reports.py           # Result reporting
```

### Frontend Structure

```
frontend/
├── package.json
├── pnpm-lock.yaml
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
│
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── (dashboard)/     # Dashboard routes
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── documents/
│   │   │   ├── conversations/
│   │   │   ├── analytics/
│   │   │   └── settings/
│   │   └── api/             # API routes (if needed)
│   │
│   ├── components/          # React components
│   │   ├── ui/              # shadcn/ui components
│   │   ├── layout/          # Layout components
│   │   ├── documents/       # Document components
│   │   ├── chat/            # Chat components
│   │   └── common/          # Shared components
│   │
│   ├── hooks/               # Custom hooks
│   │   ├── useDocuments.ts
│   │   ├── useChat.ts
│   │   └── useAuth.ts
│   │
│   ├── lib/                 # Utilities
│   │   ├── api.ts           # API client
│   │   ├── utils.ts         # Helper functions
│   │   └── constants.ts
│   │
│   ├── providers/           # Context providers
│   │   ├── QueryProvider.tsx
│   │   └── ThemeProvider.tsx
│   │
│   └── types/               # TypeScript types
│       ├── api.ts
│       └── models.ts
│
└── public/                  # Static assets
```

### Widget Package Structure

```
packages/widget/
├── package.json
├── vite.config.ts
├── tsconfig.json
│
├── src/
│   ├── index.ts             # Package entry
│   ├── SimbaWidget.tsx      # Main component
│   ├── components/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageInput.tsx
│   │   ├── TypingIndicator.tsx
│   │   └── FeedbackPanel.tsx
│   │
│   ├── hooks/
│   │   ├── useSimba.ts
│   │   └── useMessages.ts
│   │
│   ├── styles/
│   │   └── widget.css       # Scoped styles
│   │
│   ├── types/
│   │   └── index.ts
│   │
│   └── utils/
│       └── api.ts
│
└── dist/                    # Build output
    ├── widget.js
    ├── widget.css
    └── widget.d.ts
```

---

## Data Models

### Core Entities

```python
# Document
class Document:
    id: UUID
    name: str
    file_path: str
    mime_type: str
    size_bytes: int
    status: DocumentStatus  # pending, parsing, ready, failed
    metadata: dict
    created_at: datetime
    updated_at: datetime

# Chunk (document segment)
class Chunk:
    id: UUID
    document_id: UUID
    content: str
    embedding: Vector[1536]  # dimension depends on model
    metadata: dict
    position: int
    created_at: datetime

# Conversation
class Conversation:
    id: UUID
    external_id: str | None  # customer's reference
    metadata: dict
    created_at: datetime
    updated_at: datetime

# Message
class Message:
    id: UUID
    conversation_id: UUID
    role: MessageRole  # user, assistant, system
    content: str
    sources: list[ChunkReference]
    feedback: Feedback | None
    latency_ms: int
    created_at: datetime

# Feedback
class Feedback:
    id: UUID
    message_id: UUID
    rating: int  # 1-5 or thumbs up/down
    reason: str | None
    created_at: datetime
```

### Evaluation Entities

```python
# EvalRun
class EvalRun:
    id: UUID
    name: str
    config: dict
    status: EvalStatus
    started_at: datetime
    completed_at: datetime | None

# EvalResult
class EvalResult:
    id: UUID
    run_id: UUID
    metric_name: str
    value: float
    metadata: dict
    created_at: datetime
```

---

## API Endpoints

### Chat

```
POST   /api/v1/chat/message
       Send a message and get response

POST   /api/v1/chat/stream
       Send a message with streaming response

GET    /api/v1/chat/conversations
       List all conversations

GET    /api/v1/chat/conversations/{id}
       Get conversation details

DELETE /api/v1/chat/conversations/{id}
       Delete conversation
```

### Documents

```
GET    /api/v1/documents
       List all documents

POST   /api/v1/documents
       Upload new document

GET    /api/v1/documents/{id}
       Get document details

DELETE /api/v1/documents/{id}
       Delete document

POST   /api/v1/documents/{id}/parse
       Trigger document parsing

GET    /api/v1/documents/{id}/chunks
       Get document chunks
```

### Retrieval

```
POST   /api/v1/retrieval/search
       Semantic search across documents

POST   /api/v1/retrieval/hybrid
       Hybrid (semantic + keyword) search
```

### Health

```
GET    /api/v1/health
       Basic health check

GET    /api/v1/health/ready
       Readiness probe (DB, Redis, etc.)
```

---

## Security Architecture

### Authentication

```
Widget → Backend:
- API Key in header: X-API-Key
- Rate limited per key
- Key scoped to organization

Dashboard → Backend:
- JWT tokens (access + refresh)
- Stored in httpOnly cookies
- Short-lived access (15min)
- Long-lived refresh (7 days)
```

### Authorization

```
RBAC Levels:
- admin: Full access
- member: Read/write documents, conversations
- viewer: Read-only access

Widget permissions:
- Can only access own organization's data
- Rate limited
- No admin endpoints
```

### Data Protection

```
At Rest:
- PostgreSQL encryption
- Object storage encryption (S3/MinIO)

In Transit:
- TLS 1.3 everywhere
- HTTPS only in production

Sensitive Data:
- API keys hashed (argon2)
- PII minimized in logs
- Audit trail for access
```

---

## Deployment Architecture

### Development

```
┌─────────────────────────────────────────────────┐
│  Local Machine                                  │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Frontend │  │ Backend  │  │  Widget  │     │
│  │ :3000    │  │ :8000    │  │ :5173    │     │
│  └──────────┘  └──────────┘  └──────────┘     │
│                                                 │
│  ┌────────────────────────────────────────┐    │
│  │  Docker Compose                         │    │
│  │  ┌──────────┐  ┌──────────┐            │    │
│  │  │PostgreSQL│  │  Redis   │            │    │
│  │  │ :5432    │  │  :6379   │            │    │
│  │  └──────────┘  └──────────┘            │    │
│  └────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### Production

```
┌───────────────────────────────────────────────────────────────┐
│  Cloud Infrastructure                                          │
│                                                                │
│  ┌─────────────────────┐                                      │
│  │   CDN (CloudFlare)  │   ◄── Widget JS/CSS                  │
│  └──────────┬──────────┘                                      │
│             │                                                  │
│  ┌──────────▼──────────┐                                      │
│  │   Load Balancer     │                                      │
│  └──────────┬──────────┘                                      │
│             │                                                  │
│  ┌──────────┴──────────┐                                      │
│  │                     │                                      │
│  ▼                     ▼                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  API Pod 1  │  │  API Pod 2  │  │  API Pod N  │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                │
│  ┌─────────────────────────────────────────────────┐          │
│  │  Worker Pods (Celery)                           │          │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │          │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker N │      │          │
│  │  └──────────┘  └──────────┘  └──────────┘      │          │
│  └─────────────────────────────────────────────────┘          │
│                                                                │
│  ┌─────────────────────────────────────────────────┐          │
│  │  Data Layer                                     │          │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │          │
│  │  │PostgreSQL│  │  Redis   │  │   S3     │      │          │
│  │  │(Primary/ │  │(Cluster) │  │(Objects) │      │          │
│  │  │ Replica) │  │          │  │          │      │          │
│  │  └──────────┘  └──────────┘  └──────────┘      │          │
│  └─────────────────────────────────────────────────┘          │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

---

## Evaluation Framework

### Required Metrics

Every AI response must be evaluated:

```python
class ResponseEvaluation:
    # Quality metrics
    relevance_score: float      # 0-1, does it answer the question?
    accuracy_score: float       # 0-1, is information correct?
    completeness_score: float   # 0-1, is answer complete?
    citation_score: float       # 0-1, are sources used properly?

    # Performance metrics
    latency_ms: int             # Total response time
    retrieval_latency_ms: int   # Time to retrieve context
    generation_latency_ms: int  # Time to generate response

    # Retrieval metrics
    mrr: float                  # Mean Reciprocal Rank
    ndcg: float                 # Normalized Discounted Cumulative Gain
    recall_at_k: float          # Recall at K documents
```

### Evaluation Pipeline

```
Request → Retrieve → Generate → Evaluate → Log → Return

┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Receive │ -> │ Retrieve │ -> │ Generate │ -> │ Evaluate │
│ Query   │    │ Context  │    │ Response │    │ Quality  │
└─────────┘    └──────────┘    └──────────┘    └──────────┘
                                                     │
                                                     ▼
                                              ┌──────────┐
                                              │   Log    │
                                              │ Metrics  │
                                              └──────────┘
```

### Running Evaluations

```bash
# Run full eval suite
uv run python -m simba.evals run --config eval_config.yaml

# Run specific metrics
uv run python -m simba.evals run --metrics relevance,accuracy

# Generate report
uv run python -m simba.evals report --format html --output report.html
```

---

## Development Workflow

### Setup

```bash
# Clone repository
git clone https://github.com/GitHamza0206/simba.git
cd simba

# Backend setup
uv sync
cp .env.example .env
# Edit .env with your values

# Start dependencies
docker compose up -d postgres redis

# Run backend
uv run simba server

# Frontend setup (separate terminal)
cd frontend
pnpm install
pnpm dev

# Widget development (separate terminal)
cd packages/widget
pnpm install
pnpm dev
```

### Testing

```bash
# Backend tests
uv run pytest
uv run pytest --cov=simba --cov-report=html

# Frontend tests
cd frontend && pnpm test

# Widget tests
cd packages/widget && pnpm test

# E2E tests
pnpm test:e2e
```

### Building

```bash
# Build widget for npm
cd packages/widget
pnpm build
# Output in dist/

# Build frontend
cd frontend
pnpm build

# Build Docker images
docker compose build
```

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/simba

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
SECRET_KEY=your-secret-key
API_KEY_SALT=your-salt

# Feature Flags
ENABLE_STREAMING=true
ENABLE_EVALS=true
```

### Application Config

```yaml
# config.yaml
project:
  name: Simba
  version: 2.0.0
  api_version: /api/v1

embedding:
  provider: openai  # or huggingface
  model: text-embedding-3-small
  dimensions: 1536

llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.1
  max_tokens: 1024

retrieval:
  method: hybrid
  k: 5
  score_threshold: 0.7

vector_store:
  provider: pgvector
  collection: simba_vectors
```

---

## Monitoring

### Health Checks

```python
@router.get("/health")
async def health():
    return {"status": "healthy"}

@router.get("/health/ready")
async def ready(db: Session, redis: Redis):
    checks = {
        "database": await check_db(db),
        "redis": await check_redis(redis),
        "vector_store": await check_vectors(),
    }
    all_healthy = all(checks.values())
    return {"ready": all_healthy, "checks": checks}
```

### Metrics to Track

```
# Application metrics
simba_requests_total
simba_request_duration_seconds
simba_active_conversations
simba_messages_total

# AI metrics
simba_eval_relevance_score
simba_eval_accuracy_score
simba_retrieval_latency_seconds
simba_generation_latency_seconds

# Infrastructure
simba_db_connections
simba_redis_memory_bytes
simba_celery_tasks_queued
```

### Logging

```python
# Structured logging format
{
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "INFO",
    "message": "Chat response generated",
    "request_id": "uuid",
    "conversation_id": "uuid",
    "latency_ms": 1234,
    "eval_scores": {
        "relevance": 0.95,
        "accuracy": 0.92
    }
}
```
