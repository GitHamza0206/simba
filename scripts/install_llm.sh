#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"; exit 1; }

# Read model from config
log "Reading config file..."
if [ ! -f "config.yaml" ]; then
    error "Config file not found in current directory"
fi

MODEL=$(grep -A1 'llm:' config.yaml | grep 'model_name:' | awk '{print $2}' | tr -d '"')

# Pull the model in Ollama container
log "Installing model: $MODEL in Ollama container..."
docker exec ollama ollama pull $MODEL

log "Model installation complete! ✨" 