-- Migration to create embeddings table in Supabase
-- This table is designed to work with pgvector and LangChain's PGVector implementation

-- First ensure pgvector extension exists
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the embeddings table
CREATE TABLE IF NOT EXISTS chunks_embeddings (
    id TEXT PRIMARY KEY,  -- Changed from UUID to TEXT to match LangChain's string UUIDs
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}'::jsonb, -- Stores LangChain Document object (content + metadata)
    embedding vector(1536), -- OpenAI's default embedding size
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_data ON chunks_embeddings USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to automatically update the updated_at column
CREATE TRIGGER update_chunks_embeddings_updated_at
    BEFORE UPDATE ON chunks_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add RLS policies
ALTER TABLE chunks_embeddings ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Enable read access for all users" ON chunks_embeddings
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for authenticated users only" ON chunks_embeddings
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable update for authenticated users only" ON chunks_embeddings
    FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Enable delete for authenticated users only" ON chunks_embeddings
    FOR DELETE USING (auth.role() = 'authenticated');

-- Create a view for easier querying of chunks with their documents
CREATE OR REPLACE VIEW document_chunks AS
SELECT 
    c.id as chunk_id,
    c.document_id,
    c.data->>'page_content' as content,
    c.data->'metadata' as metadata,
    d.data as document_data,
    c.created_at,
    c.updated_at
FROM chunks_embeddings c
JOIN documents d ON c.document_id = d.id;

-- Confirm successful creation
DO $$
BEGIN
    RAISE NOTICE 'Chunks embeddings table and related objects created successfully';
END $$; 