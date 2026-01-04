# Simba - Development Guidelines

This document provides guidelines for Claude Code when working on the Simba repository.

## Project Overview

Simba is an open-source customer service assistant with a RAG (Retrieval-Augmented Generation) pipeline. It consists of:

- **Backend**: Python FastAPI server with LangChain/LangGraph
- **Frontend**: Next.js 15 dashboard with React 19
- **NPM Package**: `simba-chat` widget in `packages/simba-chat/`

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, LangChain, LangGraph |
| Frontend | Next.js 15, React 19, Tailwind CSS, Radix UI |
| Package Manager (Python) | uv |
| Package Manager (Frontend) | pnpm |
| Package Manager (simba-chat) | bun |
| Vector Store | Qdrant |
| Task Queue | Celery + Redis |
| Object Storage | MinIO |
| Database | PostgreSQL |

## Directory Structure

```
simba/
├── simba/                    # Python backend
│   ├── api/                  # FastAPI routes
│   ├── services/             # Business logic
│   ├── core/                 # Config, Celery
│   └── evaluation/           # RAG evaluation
├── frontend/                 # Next.js dashboard
│   └── src/
│       ├── app/              # App router pages
│       ├── components/       # React components
│       └── hooks/            # Custom hooks
├── packages/
│   └── simba-chat/           # NPM package
├── docker/                   # Docker configs
└── Makefile                  # Dev commands
```

## Installation & Setup

### Backend (Python)

```bash
# Install dependencies with uv
uv sync

# Install with dev dependencies
uv sync --dev
```

### Frontend (Next.js)

```bash
cd frontend
pnpm install
```

### NPM Package (simba-chat)

```bash
cd packages/simba-chat
bun install
```

## Running Services

### Quick Start (Docker)

```bash
# Start infrastructure services (Redis, Postgres, Qdrant, MinIO)
make services

# Start the API server (in another terminal)
make server

# Start Celery worker for document ingestion (in another terminal)
make celery
```

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make server` | Run FastAPI server with hot reload |
| `make celery` | Run Celery worker for document ingestion |
| `make services` | Start infrastructure (Redis, Postgres, Qdrant, MinIO) |
| `make up` | Start all services including server via Docker |
| `make down` | Stop all Docker services |
| `make logs` | View Docker logs |
| `make evaluate` | Run RAG evaluation |
| `make evaluate-rerank` | Run RAG evaluation with reranking |

### Frontend Development

```bash
cd frontend
pnpm dev          # Start dev server on localhost:3000
pnpm build        # Production build
pnpm typecheck    # Run TypeScript checks
pnpm lint         # Run ESLint
```

### NPM Package Development

```bash
cd packages/simba-chat
bun run dev       # Watch mode
bun run build     # Build for production
bun run typecheck # Type check
```

## API Endpoints

The backend runs on `localhost:8000`. Key endpoints:

- `POST /api/v1/conversations/chat/stream` - Streaming chat (SSE)
- `GET /api/v1/collections` - List collections
- `POST /api/v1/documents` - Upload documents
- `GET /api/v1/health` - Health check

## Environment Variables

Create a `.env` file in the root:

```bash
OPENAI_API_KEY=your_openai_api_key

# Optional - defaults work for local dev
QDRANT_HOST=localhost
QDRANT_PORT=6333
MINIO_ENDPOINT=localhost:9000
CELERY_BROKER_URL=redis://localhost:6379/0
```

## Code Style

### Python
- Use `ruff` for linting and formatting
- Type hints required
- Line length: 100 chars

### TypeScript/React
- Use ESLint + Prettier
- Prefer functional components with hooks
- Use TypeScript strict mode

## Testing

```bash
# Python tests
uv run pytest

# TypeScript type checking
cd frontend && pnpm typecheck
```

## Common Tasks

### Adding a new API endpoint
1. Create route in `simba/api/routes/`
2. Register in `simba/api/app.py`
3. Add service logic in `simba/services/`

### Adding a frontend component
1. Create component in `frontend/src/components/`
2. Use Tailwind for styling
3. Follow existing patterns in `components/ui/`

### Building the NPM package
```bash
cd packages/simba-chat
bun run build
# Output in dist/
```

## Services Ports

| Service | Port |
|---------|------|
| API Server | 8000 |
| Frontend | 3000 |
| Redis | 6379 |
| PostgreSQL | 5432 |
| Qdrant | 6333, 6334 |
| MinIO | 9000 (API), 9001 (Console) |

## Pre-commit Checks

**IMPORTANT**: Always run linters before committing changes:

```bash
# Python - run ruff linter and formatter
uv run ruff check --fix .
uv run ruff format .

# Frontend - run ESLint and TypeScript checks
cd frontend && pnpm lint && pnpm type-check
```

Or run all checks via pre-commit:
```bash
uv run pre-commit run --all-files
```
