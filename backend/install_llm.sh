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

MODEL=$(python3 -c '
import yaml
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
        print(config["llm"]["model_name"])
except Exception as e:
    print(f"Error: {e}")
    exit(1)
')

if [ $? -ne 0 ] || [ -z "$MODEL" ]; then
    error "Failed to read model name from config"
fi

# Pull the model in Ollama container
log "Installing model: $MODEL in Ollama container..."
if ! docker exec -it ollama ollama pull "$MODEL"; then
    error "Failed to pull model: $MODEL"
fi

log "Model installation complete! ✨" 