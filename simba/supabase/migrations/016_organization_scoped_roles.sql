-- =============================================================
-- Section 16: Organization-Scoped Roles and Schema Improvements
-- =============================================================

-- Step 1: Create new organization-scoped user_roles table
DROP TABLE IF EXISTS user_roles CASCADE;

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    role_id INTEGER NOT NULL REFERENCES roles(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, organization_id, role_id)
);

-- Add indexes for better performance
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_org_id ON user_roles(organization_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

-- Enable RLS on user_roles
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_roles
CREATE POLICY "Users can view roles in their organizations" ON user_roles
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Step 2: Add organization_id to chunks_embeddings
ALTER TABLE chunks_embeddings
    ADD COLUMN organization_id UUID REFERENCES organizations(id);

CREATE INDEX idx_chunks_embeddings_org_id ON chunks_embeddings(organization_id);

-- Update RLS on chunks_embeddings
DROP POLICY IF EXISTS "Users can view their own embeddings" ON chunks_embeddings;
CREATE POLICY "Users can view embeddings in their organizations" ON chunks_embeddings
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Step 3: Create org_settings table
CREATE TABLE org_settings (
    organization_id UUID PRIMARY KEY REFERENCES organizations(id),
    max_users INT,
    max_storage_gb INT,
    plan_name TEXT,
    features JSONB,
    style_overrides JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS on org_settings
ALTER TABLE org_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies for org_settings
CREATE POLICY "Users can view settings in their organizations" ON org_settings
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Step 4: Create audit_logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    changed_by UUID NOT NULL REFERENCES auth.users(id),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB
);

CREATE INDEX idx_audit_logs_org_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_changed_by ON audit_logs(changed_by);
CREATE INDEX idx_audit_logs_changed_at ON audit_logs(changed_at);

-- Enable RLS on audit_logs
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for audit_logs
CREATE POLICY "Users can view audit logs in their organizations" ON audit_logs
    FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

-- Grant necessary permissions
GRANT SELECT, INSERT ON user_roles TO authenticated;
GRANT SELECT ON user_roles TO anon;
GRANT SELECT ON org_settings TO authenticated;
GRANT SELECT ON org_settings TO anon;
GRANT SELECT ON audit_logs TO authenticated;
GRANT SELECT ON audit_logs TO anon;

-- Create function to automatically update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger for org_settings updated_at
CREATE TRIGGER update_org_settings_updated_at
    BEFORE UPDATE ON org_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create audit log trigger function
CREATE OR REPLACE FUNCTION process_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    old_data_val JSONB;
    new_data_val JSONB;
    org_id_val UUID;
BEGIN
    -- Get organization_id based on the table
    IF TG_TABLE_NAME = 'organizations' THEN
        org_id_val = COALESCE(NEW.id, OLD.id);
    ELSE
        org_id_val = COALESCE(NEW.organization_id, OLD.organization_id);
    END IF;

    IF (TG_OP = 'DELETE') THEN
        old_data_val = to_jsonb(OLD);
        new_data_val = NULL;
    ELSIF (TG_OP = 'UPDATE') THEN
        old_data_val = to_jsonb(OLD);
        new_data_val = to_jsonb(NEW);
    ELSE
        old_data_val = NULL;
        new_data_val = to_jsonb(NEW);
    END IF;

    INSERT INTO audit_logs (
        organization_id,
        table_name,
        record_id,
        changed_by,
        operation,
        old_data,
        new_data
    ) VALUES (
        org_id_val,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        auth.uid(),
        TG_OP,
        old_data_val,
        new_data_val
    );

    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql' SECURITY DEFINER;

-- Add audit triggers to relevant tables
CREATE TRIGGER audit_organizations
    AFTER INSERT OR UPDATE OR DELETE ON organizations
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

CREATE TRIGGER audit_collections
    AFTER INSERT OR UPDATE OR DELETE ON collections
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

CREATE TRIGGER audit_documents
    AFTER INSERT OR UPDATE OR DELETE ON documents
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

DO $$ 
BEGIN
    RAISE NOTICE 'Organization-scoped roles and schema improvements have been added successfully';
END $$; 