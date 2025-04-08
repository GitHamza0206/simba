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


-- =============================================================
-- Section 2: Roles & Permissions
-- =============================================================

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,          -- e.g., 'admin', 'user'
  description TEXT,                   -- Human-readable description
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,          -- e.g., 'users:read'
  description TEXT,                   -- Human-readable description
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Many-to-many mapping: Role-Permissions
CREATE TABLE IF NOT EXISTS role_permissions (
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

-- Many-to-many mapping: User-Roles
CREATE TABLE IF NOT EXISTS user_roles (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

-- Insert default roles
INSERT INTO roles (name, description)
VALUES 
  ('admin', 'Full system access with all permissions'),
  ('user', 'Regular user with limited access')
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions
INSERT INTO permissions (name, description)
VALUES
  ('users:read',   'Can view user information'),
  ('users:write',  'Can modify user information'),
  ('users:delete', 'Can delete users'),
  ('roles:read',   'Can view roles'),
  ('roles:write',  'Can modify roles'),
  ('roles:delete', 'Can delete roles')
ON CONFLICT (name) DO NOTHING;

-- Assign all permissions to admin role
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Assign basic permissions to user role (only 'users:read')
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p
WHERE r.name = 'user' AND p.name IN ('users:read')
ON CONFLICT DO NOTHING;

-- Helper functions to check user roles and permissions
CREATE OR REPLACE FUNCTION user_has_role(user_uuid UUID, role_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM user_roles ur
    JOIN roles r ON r.id = ur.role_id
    WHERE ur.user_id = user_uuid
      AND r.name = role_name
  );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION user_has_permission(user_uuid UUID, permission_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM user_roles ur
    JOIN role_permissions rp ON rp.role_id = ur.role_id
    JOIN permissions p ON p.id = rp.permission_id
    WHERE ur.user_id = user_uuid
      AND p.name = permission_name
  );
END;
$$ LANGUAGE plpgsql;

-- Enable RLS on roles-related tables and create policies
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can do everything with roles" ON roles
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view roles" ON roles
    FOR SELECT
    USING (true);

CREATE POLICY "Admins can do everything with permissions" ON permissions
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view permissions" ON permissions
    FOR SELECT
    USING (true);

CREATE POLICY "Admins can do everything with role_permissions" ON role_permissions
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view role_permissions" ON role_permissions
    FOR SELECT
    USING (true);

CREATE POLICY "Admins can do everything with user_roles" ON user_roles
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view their own roles" ON user_roles
    FOR SELECT
    USING (auth.uid() = user_id OR user_has_role(auth.uid(), 'admin'));


-- =============================================================
-- Section 3: Organizations & Organization Members
-- =============================================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer', 'none')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, user_id),
    UNIQUE (organization_id, email)
);

-- Indexes for organization_members
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_email ON organization_members(email);
CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON organization_members(organization_id);

-- Enable RLS and create policies for organizations
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_select_policy ON organizations 
    FOR SELECT 
    USING (
        id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY org_insert_policy ON organizations 
    FOR INSERT 
    WITH CHECK (created_by = auth.uid());

CREATE POLICY org_update_policy ON organizations 
    FOR UPDATE 
    USING (
        id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid() AND role = 'owner'
        )
    );

CREATE POLICY org_delete_policy ON organizations 
    FOR DELETE 
    USING (
        id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid() AND role = 'owner'
        )
    );

-- Enable RLS and create policies for organization_members
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_members_select_policy ON organization_members 
    FOR SELECT 
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY org_members_insert_policy ON organization_members 
    FOR INSERT 
    WITH CHECK (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid() AND role IN ('owner', 'admin')
        )
    );

CREATE POLICY org_members_update_policy ON organization_members 
    FOR UPDATE 
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid() AND role = 'owner'
        )
    );

CREATE POLICY org_members_delete_policy ON organization_members 
    FOR DELETE 
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid() AND role = 'owner'
        )
    );


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


-- =============================================================
-- Section 5: Embeddings (chunks_embeddings) Table
-- =============================================================

-- Create the embeddings table for LangChain documents and vector data
CREATE TABLE IF NOT EXISTS chunks_embeddings (
    id TEXT PRIMARY KEY,  -- Using string UUIDs as per LangChain convention
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(1536) NOT NULL,  -- OpenAI's default embedding size is 1536 dimensions
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_document FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks_embeddings(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_user_id ON chunks_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_chunks_data ON chunks_embeddings USING GIN (data);

-- Create a HNSW index on the embedding column.
-- HNSW parameters:
--   m = 16: Controls graph connectivity (a good starting point).
--   ef_construction = 64: Balances index quality with build time.
-- Note: The distance operator "vector_cosine_ops" assumes cosine similarity is used.
--       The ef_search parameter is set during query time to adjust recall.
CREATE INDEX IF NOT EXISTS idx_chunks_embeddings_embedding_hnsw
  ON chunks_embeddings
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Additional Ingestion Recommendations:
-- For optimal ingestion of your embeddings data, consider the following:
--   • Use BULK INSERT methods or COPY BINARY when loading large volumes of embeddings.
--     (These methods are typically 5-10 times faster than individual INSERT statements.)
--   • If index build time is a concern, build the HNSW index in parallel (if your PostgreSQL version supports it),
--     which can significantly reduce construction time.
--   • Consider vector quantization techniques if storage space is a constraint
--     (be mindful that quantization may reduce recall and may require an additional re-ranking step).
--   • Always measure the recall rate during testing to ensure that your optimizations do not compromise the quality of your results.

-- Trigger to update the updated_at column for embeddings
CREATE TRIGGER update_chunks_embeddings_updated_at
    BEFORE UPDATE ON chunks_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS and create policies for chunks_embeddings
ALTER TABLE chunks_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read access for chunk owner only" ON chunks_embeddings
    FOR SELECT USING (auth.role() = 'authenticated' AND user_id = auth.uid());

CREATE POLICY "Enable insert for chunk owner only" ON chunks_embeddings
    FOR INSERT WITH CHECK (auth.role() = 'authenticated' AND user_id = auth.uid());

CREATE POLICY "Enable update for chunk owner only" ON chunks_embeddings
    FOR UPDATE USING (auth.role() = 'authenticated' AND user_id = auth.uid());

CREATE POLICY "Enable delete for chunk owner only" ON chunks_embeddings
    FOR DELETE USING (auth.role() = 'authenticated' AND user_id = auth.uid());

-- View joining chunks with their documents for easier querying
CREATE OR REPLACE VIEW document_chunks AS
SELECT 
    c.id AS chunk_id,
    c.document_id,
    c.user_id,
    c.data->>'page_content' AS content,
    c.data->'metadata' AS metadata,
    d.data AS document_data,
    c.created_at,
    c.updated_at
FROM chunks_embeddings c
JOIN documents d ON c.document_id = d.id;

DO $$
BEGIN
    RAISE NOTICE 'Chunks embeddings table and related objects created successfully';
END $$;


-- =============================================================
-- Section 6: API Keys Table
-- =============================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT NOT NULL UNIQUE,           -- Hashed API key value
    key_prefix TEXT NOT NULL,           -- For display/identification
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,                 -- User-friendly name
    roles JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- Function and trigger to update the last_used column
CREATE OR REPLACE FUNCTION update_api_key_last_used()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_used = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_api_key_usage
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    WHEN (OLD.last_used IS DISTINCT FROM NEW.last_used)
    EXECUTE FUNCTION update_api_key_last_used();

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "API keys are only visible to their creator" ON api_keys
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can only create API keys for themselves" ON api_keys
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can only update their own API keys" ON api_keys
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can only delete their own API keys" ON api_keys
    FOR DELETE USING (auth.uid() = user_id);

CREATE OR REPLACE FUNCTION is_valid_api_key(api_key TEXT)
RETURNS UUID AS $$
DECLARE
    user_id_val UUID;
BEGIN
    SELECT user_id INTO user_id_val
    FROM api_keys
    WHERE key = api_key
      AND is_active = true
      AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP);
    RETURN user_id_val;
END;
$$ LANGUAGE plpgsql;


-- =============================================================
-- Section 7: Privileges & Final Notices
-- =============================================================

-- Grant ownership and privileges to postgres on relevant objects
ALTER TABLE chunks_embeddings OWNER TO postgres;
GRANT ALL PRIVILEGES ON TABLE chunks_embeddings TO postgres;

GRANT USAGE ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

DO $$ BEGIN
    RAISE NOTICE 'All database objects created successfully';
END $$;
