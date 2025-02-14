#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print with timestamp
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Create shared network if it doesn't exist
log "Setting up network..."
docker network create simba_network 2>/dev/null || true

# Start frontend with docker-compose
log "Starting frontend..."
cd frontend && docker-compose up -d
cd ..

# Start backend
log "Starting backend..."
cd backend && ./run.sh &
BACKEND_PID=$!
cd ..



# Show frontend logs but keep backend running
log "${BLUE}Services started! Showing frontend logs (Ctrl+C to exit)...${NC}"
cd frontend && docker-compose logs -f &
LOGS_PID=$!
cd ..

# Handle cleanup on exit
cleanup() {
    log "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $LOGS_PID 2>/dev/null
    cd frontend && docker-compose down
    cd ..
    docker network rm simba_network 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait $BACKEND_PID 