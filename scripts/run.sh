#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print with color
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Check Docker availability
if ! command -v docker &> /dev/null; then
    error "Docker is required but not installed"
fi

# Check Python and dependencies
if ! command -v python3 &> /dev/null; then
    error "Python 3 is required but not installed"
fi

# Check if required Python packages are installed
check_package() {
    python3 -c "import $1" 2>/dev/null || {
        log "Installing $1..."
        pip install $1
    }
}

# Install required packages
check_package yaml
check_package pathlib

# Make run.py executable
chmod +x run.py

# Start backend
log "Starting Simba backend..."
exec ./run.py 