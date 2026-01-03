---
description: Set up Simba project with all dependencies and services
argument-hint: [--backend|--frontend|--services|--all]
allowed-tools: Bash(uv:*), Bash(pnpm:*), Bash(bun:*), Bash(make:*), Bash(docker:*), Bash(docker-compose:*), Bash(curl:*), Read, Glob
---

# Simba Project Setup

You are setting up the Simba RAG assistant project. Follow the CLAUDE.md guidelines.

## Current Status

Check what's already installed:
- Docker services: !`docker ps --format "table {{.Names}}\t{{.Status}}" 2>&1 | head -10 || echo "Docker not running"`
- uv version: !`uv --version 2>&1 || echo "uv not installed"`
- pnpm version: !`pnpm --version 2>&1 || echo "pnpm not installed"`
- bun version: !`bun --version 2>&1 || echo "bun not installed"`

## Arguments

The user specified: $ARGUMENTS

## Setup Instructions

Based on the argument provided, perform the appropriate setup:

### If "--backend" or "--all" or no argument:

1. **Install Python dependencies**:
   ```bash
   uv sync
   ```

2. **Verify Python installation**:
   ```bash
   uv pip list | head -20
   ```

### If "--frontend" or "--all" or no argument:

1. **Install Next.js frontend dependencies**:
   ```bash
   cd frontend && pnpm install
   ```

2. **Install simba-chat NPM package dependencies**:
   ```bash
   cd packages/simba-chat && bun install
   ```

### If "--services" or "--all":

1. **Check for .env file** - if missing, create from example or prompt user for OPENAI_API_KEY

2. **Start infrastructure services**:
   ```bash
   make services
   ```
   This starts: Redis, PostgreSQL, Qdrant, MinIO

3. **Wait for services to be healthy** (about 10-15 seconds)

4. **Verify services are running**:
   ```bash
   docker ps
   ```

## Post-Setup Instructions

After setup completes, inform the user:

1. **To start the API server** (in a new terminal):
   ```bash
   make server
   ```

2. **To start Celery worker** for document ingestion (in another terminal):
   ```bash
   make celery
   ```

3. **To start the frontend** (in another terminal):
   ```bash
   cd frontend && pnpm dev
   ```

4. **Service URLs**:
   - API Server: http://localhost:8000
   - Frontend: http://localhost:3000
   - MinIO Console: http://localhost:9001
   - Qdrant Dashboard: http://localhost:6333/dashboard

## Environment Variables

If `.env` doesn't exist, create one with at minimum:
```
OPENAI_API_KEY=your_openai_api_key
```

## Troubleshooting

- If Docker services fail: Check if Docker Desktop is running
- If port conflicts: Stop existing services on ports 6379, 5432, 6333, 9000
- If uv not found: Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- If pnpm not found: Install with `npm install -g pnpm`
- If bun not found: Install with `curl -fsSL https://bun.sh/install | bash`

Provide a clear summary at the end showing what was set up and next steps.
