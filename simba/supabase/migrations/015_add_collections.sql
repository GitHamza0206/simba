-- =============================================================
-- Section 15: Add Collections Support
-- =============================================================

-- Create collections table
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    description TEXT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    parent_collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Add index for faster lookups
CREATE INDEX idx_collections_org_id ON collections(organization_id);
CREATE INDEX idx_collections_parent_id ON collections(parent_collection_id);

-- Modify documents table to support collections
ALTER TABLE documents 
    ADD COLUMN collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

-- Add indexes for documents
CREATE INDEX idx_documents_collection_id ON documents(collection_id);
CREATE INDEX idx_documents_org_id ON documents(organization_id);

-- Update RLS policies
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view collections in their organization
CREATE POLICY "Users can view collections in their organization" ON collections
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Policy: Users can create collections in their organization
CREATE POLICY "Users can create collections in their organization" ON collections
    FOR INSERT
    WITH CHECK (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Policy: Users can update collections in their organization
CREATE POLICY "Users can update collections in their organization" ON collections
    FOR UPDATE
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Policy: Users can delete collections in their organization
CREATE POLICY "Users can delete collections in their organization" ON collections
    FOR DELETE
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Grant permissions to roles
GRANT SELECT, INSERT, UPDATE, DELETE ON collections TO authenticated;
GRANT SELECT ON collections TO anon;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger for updated_at
CREATE TRIGGER update_collections_updated_at
    BEFORE UPDATE ON collections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add function to ensure collection hierarchy integrity
CREATE OR REPLACE FUNCTION check_collection_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if parent collection exists and belongs to the same organization
    IF NEW.parent_collection_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM collections 
            WHERE id = NEW.parent_collection_id 
            AND organization_id = NEW.organization_id
        ) THEN
            RAISE EXCEPTION 'Parent collection must exist and belong to the same organization';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger for collection hierarchy check
CREATE TRIGGER check_collection_hierarchy_trigger
    BEFORE INSERT OR UPDATE ON collections
    FOR EACH ROW
    EXECUTE FUNCTION check_collection_hierarchy();

DO $$ 
BEGIN
    RAISE NOTICE 'Collections support has been added successfully';
END $$; 