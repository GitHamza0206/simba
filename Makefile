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

# Stop all services
down:
	@echo "Stopping services..."
	@docker compose -f docker/docker-compose.yml down
	@echo "Services stopped."

# Show logs
logs:
	@docker compose -f docker/docker-compose.yml logs -f

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
	@echo "  make server         - Run server with reload"
	@echo "  make celery         - Run Celery worker locally"
	@echo "  make up             - Start all services (docker-compose)"
	@echo "  make services       - Start infrastructure only (redis, postgres, qdrant, minio)"
	@echo "  make down           - Stop all services"
	@echo "  make logs           - View logs"
	@echo "  make evaluate       - Run RAG accuracy evaluation"
	@echo "  make evaluate-rerank - Run RAG evaluation with reranking"

.PHONY: server celery up services down logs help evaluate evaluate-rerank
