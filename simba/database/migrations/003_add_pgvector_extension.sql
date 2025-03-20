-- Add pgvector extension to PostgreSQL
-- This migration adds the pgvector extension to the database
-- to enable vector similarity search capabilities

-- Check if the extension already exists and create it if not
CREATE EXTENSION IF NOT EXISTS vector;

-- Confirm the extension is installed
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension installed successfully';
END $$; 