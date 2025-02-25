# Simplified Makefile for Simba Docker Build and Deployment

# Variables with sensible defaults
DEVICE ?= auto
PLATFORM ?= auto
IMAGE_NAME ?= simba
IMAGE_TAG ?= latest

# Auto-detect device type
ifeq ($(DEVICE),auto)
	ifeq ($(shell uname -m),arm64)
		ifeq ($(shell uname -s),Darwin)
			DEVICE := mps
		else
			DEVICE := cpu
		endif
	else
		ifneq ($(shell which nvidia-smi 2>/dev/null),)
			DEVICE := cuda
		else
			DEVICE := cpu
		endif
	endif
endif

# Auto-detect platform
ifeq ($(PLATFORM),auto)
	ifeq ($(shell uname -m),arm64)
		DOCKER_PLATFORM := linux/arm64
	else
		DOCKER_PLATFORM := linux/amd64
	endif
else ifeq ($(PLATFORM),arm64)
	DOCKER_PLATFORM := linux/arm64
else ifeq ($(PLATFORM),amd64)
	DOCKER_PLATFORM := linux/amd64
else
	$(error Invalid PLATFORM. Must be one of: auto, arm64, amd64)
endif

# Set device-specific options
ifeq ($(DEVICE),cuda)
	USE_GPU := true
	RUNTIME := nvidia
	ifeq ($(DOCKER_PLATFORM),linux/arm64)
		$(error CUDA device is not supported on ARM architecture)
	endif
else ifeq ($(DEVICE),mps)
	USE_GPU := true
	RUNTIME :=
	ifneq ($(DOCKER_PLATFORM),linux/arm64)
		$(error MPS device is only supported on ARM architecture)
	endif
else
	USE_GPU := false
	RUNTIME :=
endif

# Derived variables
FULL_IMAGE_NAME = $(IMAGE_NAME):$(IMAGE_TAG)

# Simple network setup
setup-network:
	@echo "Setting up Docker network..."
	@docker network inspect simba_network >/dev/null 2>&1 || docker network create simba_network

# Setup Buildx builder
setup-builder:
	@echo "Setting up Buildx builder..."
	@docker buildx rm simba-builder 2>/dev/null || true
	@docker buildx create --name simba-builder \
		--driver docker-container \
		--driver-opt "image=moby/buildkit:buildx-stable-1" \
		--driver-opt "network=host" \
		--buildkitd-flags '--allow-insecure-entitlement security.insecure' \
		--bootstrap --use

# Build image
build: setup-network setup-builder
	@echo "Building Docker image..."
	@docker buildx build --builder simba-builder \
		--platform ${DOCKER_PLATFORM} \
		--build-arg USE_GPU=${USE_GPU} \
		--build-arg TARGETARCH=${TARGETARCH} \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		-t ${IMAGE_NAME}:${IMAGE_TAG} \
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
		DEVICE=${DEVICE} RUNTIME="" RUN_OLLAMA=none docker compose -f docker/docker-compose.yml up -d; \
	fi
	@echo "Containers started successfully!"

# Down command - keep this part
down:
	@echo "Stopping containers..."
	@docker compose -f docker/docker-compose.yml down
	@echo "Containers stopped."

# Restart command - keep this part
restart: down up

# Clean everything
clean: down
	@echo "Cleaning Docker resources..."
	@docker network rm simba_network 2>/dev/null || true
	@docker volume rm docker_redis_data docker_ollama_models 2>/dev/null || true
	@echo "Cleanup complete!"

# Show logs
logs:
	@docker compose -f docker/docker-compose.yml logs -f

# One-step build and run
run: build up

# Show help
help:
	@echo "Simba Docker Commands:"
	@echo "  make build         - Build Docker image"
	@echo "  make up            - Start containers"
	@echo "  make down          - Stop containers"
	@echo "  make restart       - Restart all containers"
	@echo "  make clean         - Clean up Docker resources"
	@echo "  make logs          - View logs"
	@echo ""
	@echo "Options:"
	@echo "  DEVICE=cpu|cuda|mps|auto   (current: $(DEVICE))"
	@echo "  PLATFORM=amd64|arm64|auto  (current: $(PLATFORM))"
	@echo "  Current platform: $(DOCKER_PLATFORM)"

# Add these commands for convenience
ollama-enable:
	@ENABLE_OLLAMA=true $(MAKE) up

ollama-disable:
	@ENABLE_OLLAMA=false $(MAKE) up

.PHONY: setup-network setup-builder build up down restart clean logs run help ollama-enable ollama-disable
