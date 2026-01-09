# Makefile for Simba

# Run Celery worker
celery:
	@echo "Starting Celery worker..."
	@uv run celery -A simba.core.celery_config.celery_app worker --loglevel=info -Q ingestion

# Run server with reload
server:
	@echo "Starting server with reload..."
	@uv run uvicorn simba.api.app:app --reload

# Run Better Auth database migrations
migrate:
	@echo "Running Better Auth migrations..."
	@cd frontend && DATABASE_URL=postgresql://simba:simba@localhost:5432/simba npx @better-auth/cli migrate --yes
	@echo "Migrations complete!"

# Start all services for local development
up:
	@echo "Starting backend services..."
	@docker compose -f docker/docker-compose.yml up -d
	@echo "Backend services started!"
	@echo "  - Server:   localhost:8000"
	@echo "  - Celery:   running"
	@echo "  - Redis:    localhost:6379"
	@echo "  - Postgres: localhost:5432"
	@echo "  - Qdrant:   localhost:6333"
	@echo "  - MinIO:    localhost:9000 (console: localhost:9001)"
	@echo ""
	@echo "Waiting for Postgres to be ready..."
	@sleep 5
	@echo "Running Better Auth migrations..."
	@cd frontend && DATABASE_URL=postgresql://simba:simba@localhost:5432/simba npx @better-auth/cli migrate --yes || true
	@echo ""
	@echo "Starting frontend..."
	@cd frontend && pnpm dev

# Start all services and rebuild images
build:
	@echo "Rebuilding and starting backend services..."
	@docker compose -f docker/docker-compose.yml up -d --build
	@echo "Backend services rebuilt and started!"
	@echo "  - Server:   localhost:8000"
	@echo "  - Celery:   running"
	@echo "  - Redis:    localhost:6379"
	@echo "  - Postgres: localhost:5432"
	@echo "  - Qdrant:   localhost:6333"
	@echo "  - MinIO:    localhost:9000 (console: localhost:9001)"
	@cd frontend && pnpm dev

# Start infrastructure services only (for local development)
infra services:
	@echo "Starting infrastructure services..."
	@docker compose -f docker/docker-compose.yml up -d redis postgres qdrant minio
	@echo "Infrastructure services started!"
	@echo "  - Redis:    localhost:6379"
	@echo "  - Postgres: localhost:5432"
	@echo "  - Qdrant:   localhost:6333"
	@echo "  - MinIO:    localhost:9000 (console: localhost:9001)"
	@echo ""
	@echo "Waiting for Postgres to be ready..."
	@sleep 5
	@echo "Running Better Auth migrations..."
	@cd frontend && DATABASE_URL=postgresql://simba:simba@localhost:5432/simba npx @better-auth/cli migrate --yes || true

# Start all services with production docker-compose (includes frontend)
up-prod:
	@echo "Starting all production services..."
	@docker compose -f docker/docker-compose.prod.yml up -d
	@echo "Production services started!"
	@echo "  - Nginx:    localhost:80 (HTTP), localhost:443 (HTTPS)"
	@echo "  - Frontend: localhost:3000"
	@echo "  - Server:   localhost:8000"
	@echo "  - Celery:   running"
	@echo "  - Redis:    running"
	@echo "  - Postgres: running"
	@echo "  - Qdrant:   running"
	@echo "  - MinIO:    running"



# Stop all services
down:
	@echo "Stopping services..."
	@docker compose -f docker/docker-compose.yml down
	@echo "Services stopped."

# Stop all production services
down-prod:
	@echo "Stopping production services..."
	@docker compose -f docker/docker-compose.prod.yml down
	@echo "Production services stopped."

# Show logs
logs:
	@docker compose -f docker/docker-compose.yml logs -f

# Show production logs
logs-prod:
	@docker compose -f docker/docker-compose.prod.yml logs -f

# Run RAG evaluation
evaluate:
	@echo "Running RAG evaluation..."
	@uv run python -m simba.evaluation.evaluate --test-file simba/evaluation/test_queries.json --collection default

# Run RAG evaluation with reranking
evaluate-rerank:
	@echo "Running RAG evaluation with reranking..."
	@uv run python -m simba.evaluation.evaluate --test-file simba/evaluation/test_queries.json --collection default --rerank

# Show help
help:
	@echo "Simba Commands:"
	@echo "  make server          - Run server with reload"
	@echo "  make celery          - Run Celery worker locally"
	@echo "  make up              - Start backend (docker) + frontend (pnpm dev)"
	@echo "  make build           - Rebuild images and start backend services"
	@echo "  make up-prod         - Start all production services (pulls from registry)"
	@echo "  make infra           - Start infrastructure only (redis, postgres, qdrant, minio)"
	@echo "  make migrate         - Run Better Auth database migrations"
	@echo "  make down            - Stop all services"
	@echo "  make down-prod       - Stop all production services"
	@echo "  make logs            - View logs"
	@echo "  make logs-prod       - View production logs"
	@echo "  make evaluate        - Run RAG accuracy evaluation"
	@echo "  make evaluate-rerank - Run RAG evaluation with reranking"

.PHONY: server celery up build up-prod infra services down down-prod logs logs-prod help evaluate evaluate-rerank migrate
