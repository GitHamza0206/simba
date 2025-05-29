# Simplified Makefile for Simba Docker Build and Deployment

# Variables with sensible defaults
DEVICE ?= cpu

# Set platform based on architecture
ifeq ($(shell uname -m),arm64)
	DOCKER_PLATFORM := linux/arm64
else
	DOCKER_PLATFORM := linux/amd64
endif

# Free up Docker storage before building
docker-prune:
	@echo "Cleaning Docker resources to free up storage..."
	@docker system prune -f
	@docker builder prune -f

# Simple network setup
setup-network:
	@echo "Setting up Docker network..."
	@docker network inspect simba_network >/dev/null 2>&1 || docker network create simba_network

# Setup Buildx builder (preserves cache)
setup-builder:
	@echo "Setting up Buildx builder..."
	@if ! docker buildx inspect simba-builder >/dev/null 2>&1; then \
	  docker buildx create --name simba-builder \
	    --driver docker-container \
	    --driver-opt "image=moby/buildkit:buildx-stable-1" \
	    --driver-opt "network=host" \
	    --buildkitd-flags '--allow-insecure-entitlement security.insecure' \
	    --bootstrap --use; \
	else \
	  docker buildx use simba-builder; \
	fi

# Build frontend image
build-frontend:
	@echo "Building frontend Docker image..."
	@docker build -t simba-frontend:latest -f frontend/Dockerfile frontend

# Build image
build: build-frontend setup-network setup-builder
	@echo "Building backend Docker image..."
	@docker buildx build --builder simba-builder \
		--platform ${DOCKER_PLATFORM} \
		--build-arg USE_GPU=${USE_GPU} \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--progress=plain \
		-t simba-backend:latest \
		-f docker/Dockerfile \
		--load \
		.

# Updated up command with proper profile handling
up: setup-network
	@echo "Starting containers..."
	@if [ "${DEVICE}" = "cuda" ]; then \
		echo "Detected CUDA device - enabling GPU and Ollama"; \
		DEVICE=cuda RUNTIME=nvidia RUN_OLLAMA=ollama docker compose -f docker/docker-compose.yml up -d; \
	elif [ "${ENABLE_OLLAMA}" = "true" ]; then \
		echo "Enabling Ollama without GPU"; \
		DEVICE=${DEVICE} RUNTIME="" RUN_OLLAMA=ollama docker compose -f docker/docker-compose.yml up -d; \
	else \
		echo "Running without Ollama"; \
		DEVICE=${DEVICE} RUNTIME="" RUN_OLLAMA=none docker compose -f docker/docker-compose.yml up -d --force-recreate; \
	fi
	@echo "Containers started successfully!"

# Down command - keep this part
down:
	@echo "Stopping containers..."
	@docker compose -f docker/docker-compose.yml down
	@echo "Containers stopped."

# Clean everything
clean: down
	@echo "Cleaning Docker resources..."
	@docker network rm simba_network 2>/dev/null || true
	@docker volume rm docker_redis_data docker_ollama_models 2>/dev/null || true
	@docker system prune -af --volumes
	@echo "Cleanup complete!"

# Show logs
logs:
	@docker compose -f docker/docker-compose.yml logs -f

# Show help
help:
	@echo "Simba Docker Commands:"
	@echo "  make build         - Build Docker image"
	@echo "  make up            - Start containers"
	@echo "  make down          - Stop containers"
	@echo "  make clean         - Clean up Docker resources"
	@echo "  make logs          - View logs"
	@echo ""
	@echo "Options:"
	@echo "  DEVICE=cpu|cuda|auto   (current: $(DEVICE))"
	@echo "  Current platform: $(DOCKER_PLATFORM)"
	@echo ""
	@echo "Note: MPS (Metal Performance Shaders) is not supported in Docker containers."

# Push both backend and frontend images to Docker Hub
push-docker:
	@if [ -z "$(USER)" ]; then \
		echo "Error: USER is not set. Set it as an environment variable or pass it as 'make push-docker USER=yourdockerhubuser'"; \
		exit 1; \
	fi
	@echo "Tagging and pushing backend image..."
	docker tag simba-backend:latest $(USER)/simba-backend:latest
	docker push $(USER)/simba-backend:latest
	@echo "Tagging and pushing frontend image..."
	docker tag simba-frontend:latest $(USER)/simba-frontend:latest
	docker push $(USER)/simba-frontend:latest

# Run Supabase migrations and seed locally
migrate:
	@echo "Ensuring migration script is executable..."
	@chmod +x scripts/migrate_local.sh
	@echo "Running Supabase migrations and seed..."
	@cd simba && ../scripts/migrate_local.sh

# Enhanced cache version (optional improvement)
build-backend-with-cache:
	@docker buildx build --builder simba-builder \
		--platform ${DOCKER_PLATFORM} \
		--cache-from type=local,src=/tmp/.buildx-cache \
		--cache-to type=local,dest=/tmp/.buildx-cache \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		-t simba-backend:latest \
		-f docker/Dockerfile \
		--load \
		.

.PHONY: setup-network setup-builder build up down clean logs help docker-prune push-docker migrate
