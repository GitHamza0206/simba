#!/bin/bash
set -e

# Ensure script is run from the simba directory
if [ ! -d "supabase" ]; then
  echo "ERROR: Please run this script from inside the simba directory (where the supabase folder exists)."
  exit 1
fi

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Load environment variables from .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
: "${POSTGRES_HOST:?POSTGRES_HOST is not set. Please set it in your environment or .env file.}"
: "${POSTGRES_USER:?POSTGRES_USER is not set. Please set it in your environment or .env file.}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is not set. Please set it in your environment or .env file.}"
: "${POSTGRES_DB:?POSTGRES_DB is not set. Please set it in your environment or .env file.}"
: "${POSTGRES_PORT:?POSTGRES_PORT is not set. Please set it in your environment or .env file.}"

# Compose DB URL
DB_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"


if ! supabase db push --include-seed --db-url "$DB_URL"; then
    log "Migration failed. Attempting to pull current DB schema and migrations..."
    supabase db pull --db-url "$DB_URL"
    log "Retrying migration after pulling schema..."
    supabase db push --include-seed --db-url "$DB_URL"
fi

log "Migration and seed complete." 

