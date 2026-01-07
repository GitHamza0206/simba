# Makefile for Simba

# Run Celery worker
celery:
	@echo "Starting Celery worker..."
	@uv run celery -A simba.core.celery_config.celery_app worker --loglevel=info -Q ingestion

# Run server with reload
server:
	@echo "Starting server with reload..."
	@uv run uvicorn simba.api.app:app --reload

# Start all services with docker-compose
up:
	@echo "Starting all services..."
	@docker compose -f docker/docker-compose.yml up -d
	@echo "Services started!"
	@echo "  - Server:   localhost:8000"
	@echo "  - Redis:    localhost:6379"
	@echo "  - Postgres: localhost:5432"
	@echo "  - Qdrant:   localhost:6333"
	@echo "  - MinIO:    localhost:9000 (console: localhost:9001)"

# Start infrastructure services only (for local development)
services:
	@echo "Starting infrastructure services..."
	@docker compose -f docker/docker-compose.yml up -d redis postgres qdrant minio
	@echo "Infrastructure services started!"
	@echo "  - Redis:    localhost:6379"
	@echo "  - Postgres: localhost:5432"
	@echo "  - Qdrant:   localhost:6333"
	@echo "  - MinIO:    localhost:9000 (console: localhost:9001)"

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

# Start all services with local builds (for Apple Silicon / ARM64)
up-local:
	@echo "Building and starting all services locally..."
	@docker compose -f docker/docker-compose.local.yml up -d --build
	@echo "Local services started!"
	@echo "  - Nginx:    localhost:80 (HTTP), localhost:443 (HTTPS)"
	@echo "  - Frontend: localhost:3000"
	@echo "  - Server:   localhost:8000"
	@echo "  - Celery:   running"
	@echo "  - Redis:    running"
	@echo "  - Postgres: running"
	@echo "  - Qdrant:   running"
	@echo "  - MinIO:    running"

# Stop local services
down-local:
	@echo "Stopping local services..."
	@docker compose -f docker/docker-compose.local.yml down
	@echo "Local services stopped."

# Show local logs
logs-local:
	@docker compose -f docker/docker-compose.local.yml logs -f

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
	@echo "  make up              - Start all services (docker-compose)"
	@echo "  make up-prod         - Start all production services (pulls from registry)"
	@echo "  make up-local        - Build and start all services locally (for ARM64/Apple Silicon)"
	@echo "  make services        - Start infrastructure only (redis, postgres, qdrant, minio)"
	@echo "  make down            - Stop all services"
	@echo "  make down-prod       - Stop all production services"
	@echo "  make down-local      - Stop local services"
	@echo "  make logs            - View logs"
	@echo "  make logs-prod       - View production logs"
	@echo "  make logs-local      - View local logs"
	@echo "  make evaluate        - Run RAG accuracy evaluation"
	@echo "  make evaluate-rerank - Run RAG evaluation with reranking"

.PHONY: server celery up up-prod up-local services down down-prod down-local logs logs-prod logs-local help evaluate evaluate-rerank
