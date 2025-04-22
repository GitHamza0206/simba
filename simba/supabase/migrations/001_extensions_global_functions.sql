-- =============================================================
-- Section 1: Preliminaries - Extensions and Global Functions
-- =============================================================

-- Ensure pgvector extension is installed
CREATE EXTENSION IF NOT EXISTS vector;
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension installed successfully';
END $$;

-- Global helper function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql; 