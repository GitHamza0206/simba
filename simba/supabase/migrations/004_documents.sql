-- =============================================================
-- Section 4: Documents Table
-- =============================================================

-- Enum for parsing status (backward compatibility)
CREATE TYPE parsing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for JSONB performance
CREATE INDEX IF NOT EXISTS idx_documents_data ON documents USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);

-- Trigger to update the updated_at column
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS and set policies for documents
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for document owner only" ON documents
    FOR SELECT USING (auth.role() = 'authenticated' AND user_id = auth.uid());

CREATE POLICY "Enable insert for document owner only" ON documents
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' AND user_id = auth.uid());

CREATE POLICY "Enable update for document owner only" ON documents
    FOR UPDATE USING (auth.role() = 'authenticated' AND user_id = auth.uid());

CREATE POLICY "Enable delete for document owner only" ON documents
    FOR DELETE USING (auth.role() = 'authenticated' AND user_id = auth.uid());

-- View for easier querying of document details
CREATE OR REPLACE VIEW document_details AS
SELECT 
    id,
    user_id,
    data->'metadata'->>'filename' AS filename,
    data->'metadata'->>'type' AS file_type,
    (data->'metadata'->>'enabled')::boolean AS enabled,
    data->'metadata'->>'size' AS size,
    data->'metadata'->>'loader' AS loader,
    data->'metadata'->>'parser' AS parser,
    data->'metadata'->>'splitter' AS splitter,
    data->'metadata'->>'uploadedAt' AS uploaded_at,
    data->'metadata'->>'file_path' AS file_path,
    data->'metadata'->>'parsing_status' AS parsing_status,
    data->'metadata'->>'parsed_at' AS parsed_at,
    created_at,
    updated_at
FROM documents;

DO $$
BEGIN
    RAISE NOTICE 'Documents table and related objects created successfully';
END $$; 