#!/bin/bash
set -e

# Run database migrations
make migrate

# Execute the main container command
exec "$@" 