# Simba Infrastructure

Production infrastructure using managed services for reliability, scalability, and minimal ops overhead.

## Architecture

```mermaid
flowchart TB
    subgraph Cloudflare["Cloudflare (DNS/SSL/CDN)"]
        CF[DNS + Proxy]
    end

    subgraph Vercel["Vercel"]
        FE[Next.js Frontend]
    end

    subgraph FlyIO["Fly.io"]
        API[FastAPI Server]
        Worker[Celery Worker]
        PG[(Fly Postgres)]
        Tigris[(Tigris S3)]
    end

    subgraph External["External Services"]
        Upstash[(Upstash Redis)]
        Qdrant[(Qdrant Cloud)]
    end

    CF --> FE
    CF --> API
    FE -->|API calls| API
    API --> PG
    API --> Qdrant
    API --> Tigris
    API --> Upstash
    Worker --> PG
    Worker --> Qdrant
    Worker --> Tigris
    Worker --> Upstash
```

## Services Overview

| Service | Provider | Purpose |
|---------|----------|---------|
| Frontend | **Vercel** | Next.js 15 dashboard, auto-deploy from `main` |
| Backend API | **Fly.io** | FastAPI server, handles chat & document APIs |
| Celery Worker | **Fly.io** | Background document ingestion tasks |
| PostgreSQL | **Fly Postgres** | Main application database |
| Redis | **Upstash** | Celery task broker and result backend |
| Vector DB | **Qdrant Cloud** | Vector storage for RAG retrieval |
| Object Storage | **Tigris** | Document file storage (S3-compatible) |
| DNS/SSL | **Cloudflare** | Domain management, SSL, DDoS protection |

## Service Details

### Frontend (Vercel)

- **Framework**: Next.js 15 with React 19
- **Deployment**: Auto-deploy on push to `main`
- **Domain**: Custom domain via Cloudflare DNS

### Backend API (Fly.io)

- **Framework**: FastAPI with uvicorn
- **Machine**: `shared-cpu-1x`, 256MB RAM (scale as needed)
- **Region**: Primary region closest to users
- **Auto-stop**: Enabled for cost savings during low traffic

### Celery Worker (Fly.io)

- **Purpose**: Document parsing and vector embedding
- **Machine**: `shared-cpu-1x`, 512MB RAM (parsing needs more memory)
- **Scaling**: Always-on, single instance (scale for high ingestion loads)

### PostgreSQL (Fly Postgres)

- **Version**: PostgreSQL 16
- **Config**: Single node for staging, HA for production
- **Backups**: Automatic daily backups
- **Connection**: Internal Fly.io network (low latency)

### Redis (Upstash)

- **Type**: Serverless Redis
- **Purpose**: Celery broker (db 0) and result backend (db 1)
- **Pricing**: Pay-per-request, scales to zero

### Qdrant (Qdrant Cloud)

- **Purpose**: Vector database for document embeddings
- **Tier**: Free tier (1GB) for dev, paid for production
- **Connection**: HTTPS with API key authentication

### Tigris (Fly.io Object Storage)

- **Purpose**: Store uploaded documents
- **Compatibility**: S3-compatible API
- **Bucket**: `simba-documents`

### Cloudflare

- **DNS**: Manage domain records
- **Proxy**: DDoS protection, SSL termination
- **SSL**: Full (strict) mode with Cloudflare certificates

## Environment Variables

### Backend (Fly.io)

```bash
# LLM
OPENAI_API_KEY=sk-...

# Database (Fly Postgres - use internal URL)
DATABASE_URL=postgres://simba:PASSWORD@simba-db.internal:5432/simba

# Redis (Upstash)
CELERY_BROKER_URL=rediss://default:PASSWORD@REGION.upstash.io:6379/0
CELERY_RESULT_BACKEND=rediss://default:PASSWORD@REGION.upstash.io:6379/1

# Qdrant Cloud
QDRANT_HOST=CLUSTER-ID.REGION.aws.cloud.qdrant.io
QDRANT_PORT=6333
QDRANT_API_KEY=...

# Tigris (S3-compatible)
MINIO_ENDPOINT=fly.storage.tigris.dev
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=simba-documents
MINIO_SECURE=true

# CORS (allow frontend domain)
CORS_ORIGINS=["https://your-domain.com","https://simba-frontend.vercel.app"]
```

### Frontend (Vercel)

```bash
# API URL (your Fly.io app or custom domain)
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
```

## Network Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLOUDFLARE                                     │
│                     (DNS, SSL, CDN, DDoS)                               │
│                                                                          │
│   your-domain.com ──────► Fly.io API                                    │
│   app.your-domain.com ──► Vercel Frontend                               │
└─────────────────────────────────────────────────────────────────────────┘
                      │                     │
                      ▼                     ▼
        ┌─────────────────────┐   ┌─────────────────────┐
        │       VERCEL        │   │       FLY.IO        │
        │                     │   │                     │
        │   Next.js Frontend  │   │  ┌───────────────┐  │
        │                     │   │  │  FastAPI API  │  │
        └─────────────────────┘   │  └───────┬───────┘  │
                                  │          │          │
                                  │  ┌───────┴───────┐  │
                                  │  │ Celery Worker │  │
                                  │  └───────┬───────┘  │
                                  │          │          │
                                  │  ┌───────┴───────┐  │
                                  │  │ Fly Postgres  │◄─┼── Internal network
                                  │  └───────────────┘  │   (*.internal)
                                  │                     │
                                  │  ┌───────────────┐  │
                                  │  │    Tigris     │◄─┼── S3 API
                                  │  └───────────────┘  │
                                  └─────────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
              ▼                            ▼                            │
    ┌─────────────────┐          ┌─────────────────┐                   │
    │  UPSTASH REDIS  │          │  QDRANT CLOUD   │                   │
    │                 │          │                 │                   │
    │  Celery broker  │          │  Vector search  │                   │
    │  Task results   │          │  Embeddings     │                   │
    └─────────────────┘          └─────────────────┘                   │
              │                            │                            │
              └────────────────────────────┴────────────────────────────┘
                              External HTTPS connections
```

## Connections

| From | To | Protocol | Notes |
|------|-----|----------|-------|
| Frontend | API | HTTPS | Via Cloudflare proxy |
| API | Fly Postgres | TCP | Internal `.internal` network |
| API | Upstash | TLS | `rediss://` (Redis over TLS) |
| API | Qdrant Cloud | HTTPS | API key auth |
| API | Tigris | HTTPS | S3 protocol |
| Worker | Fly Postgres | TCP | Internal network |
| Worker | Upstash | TLS | Task queue |
| Worker | Qdrant Cloud | HTTPS | Vector storage |
| Worker | Tigris | HTTPS | File storage |

## Local Development

For local development, use Docker Compose to run services locally:

```bash
# Start infrastructure (Redis, Postgres, Qdrant, MinIO)
make services

# Run API server
make server

# Run Celery worker
make celery

# Run frontend
cd frontend && pnpm dev
```

The local setup uses:
- Local PostgreSQL (Docker)
- Local Redis (Docker)
- Local Qdrant (Docker)
- Local MinIO (Docker) - same S3 API as Tigris
