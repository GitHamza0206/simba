-- Migration to create documents table in Supabase
-- This table uses JSONB for flexible document storage

-- Create enum for parsing status (keeping for backward compatibility)
CREATE TYPE parsing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Create the documents table using JSONB storage
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance with JSONB
CREATE INDEX IF NOT EXISTS idx_documents_data ON documents USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);

-- Create a trigger to automatically update the updated_at column
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add RLS policies
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Create policies with user-specific access control
CREATE POLICY "Enable read access for document owner only" ON documents
    FOR SELECT USING (auth.role() = 'authenticated' AND user_id = auth.uid());

CREATE POLICY "Enable insert for document owner only" ON documents
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated'
        AND user_id = auth.uid());

CREATE POLICY "Enable update for document owner only" ON documents
    FOR UPDATE USING ( auth.role() = 'authenticated' AND user_id = auth.uid());

CREATE POLICY "Enable delete for document owner only" ON documents
    FOR DELETE USING (auth.role() = 'authenticated' AND user_id = auth.uid());

-- Create a view that extracts common fields from JSONB for easier querying
CREATE OR REPLACE VIEW document_details AS
SELECT 
    id,
    user_id,
    data->'metadata'->>'filename' as filename,
    data->'metadata'->>'type' as file_type,
    (data->'metadata'->>'enabled')::boolean as enabled,
    data->'metadata'->>'size' as size,
    data->'metadata'->>'loader' as loader,
    data->'metadata'->>'parser' as parser,
    data->'metadata'->>'splitter' as splitter,
    data->'metadata'->>'uploadedAt' as uploaded_at,
    data->'metadata'->>'file_path' as file_path,
    data->'metadata'->>'parsing_status' as parsing_status,
    data->'metadata'->>'parsed_at' as parsed_at,
    created_at,
    updated_at
FROM documents;

-- Confirm successful creation
DO $$
BEGIN
    RAISE NOTICE 'Documents table with user_id column and user-specific access created successfully';
END $$; 