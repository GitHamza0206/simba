-- Drop triggers first (in correct order)
DROP TRIGGER IF EXISTS audit_organizations_trigger ON organizations CASCADE;
DROP TRIGGER IF EXISTS audit_organization_members_trigger ON organization_members CASCADE;

-- Drop function with CASCADE to handle dependencies
DROP FUNCTION IF EXISTS process_audit_log() CASCADE;

-- Create audit logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_logs (
    id uuid PRIMARY KEY,
    organization_id uuid NOT NULL,
    table_name text NOT NULL,
    record_id uuid NOT NULL,
    changed_by uuid NOT NULL,
    changed_at timestamp with time zone DEFAULT now(),
    operation text NOT NULL,
    old_data jsonb,
    new_data jsonb
);

-- Recreate the function with the correct user ID access
CREATE OR REPLACE FUNCTION process_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    org_id_val uuid;
    old_data_val jsonb;
    new_data_val jsonb;
    current_user_id uuid;
BEGIN
    -- Get organization_id from the record if it exists
    IF TG_TABLE_NAME = 'organizations' THEN
        org_id_val := COALESCE(NEW.id, OLD.id);
    ELSE
        org_id_val := COALESCE(NEW.organization_id, OLD.organization_id);
    END IF;

    -- Convert old and new data to JSONB
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        old_data_val := row_to_json(OLD)::jsonb;
    END IF;
    
    IF TG_OP IN ('UPDATE', 'INSERT') THEN
        new_data_val := row_to_json(NEW)::jsonb;
    END IF;

    -- Get the current user ID from session context with fallback
    BEGIN
        current_user_id := current_setting('audit.user_id', true)::uuid;
        IF current_user_id IS NULL THEN
            -- Fallback to created_by if available (for inserts)
            IF TG_OP = 'INSERT' THEN
                current_user_id := NEW.created_by::uuid;
            ELSE
                RAISE EXCEPTION 'No user ID available for audit log';
            END IF;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        -- Final fallback to created_by if available
        IF TG_OP = 'INSERT' THEN
            current_user_id := NEW.created_by::uuid;
        ELSE
            RAISE EXCEPTION 'No user ID available for audit log';
        END IF;
    END;

    -- Insert audit log
    INSERT INTO audit_logs (
        id,
        organization_id,
        table_name,
        record_id,
        changed_by,
        changed_at,
        operation,
        old_data,
        new_data
    ) VALUES (
        gen_random_uuid(),
        org_id_val,
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        current_user_id,
        current_timestamp,
        TG_OP,
        old_data_val,
        new_data_val
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Ensure the audit.user_id setting is available at database level
DO $$
BEGIN
    -- Set for current database
    EXECUTE 'ALTER DATABASE ' || current_database() || ' SET audit.user_id = ''''';
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

-- Set for current session
SET audit.user_id = '';

-- Recreate the triggers
CREATE TRIGGER audit_organizations_trigger
    AFTER INSERT OR UPDATE OR DELETE ON organizations
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

CREATE TRIGGER audit_organization_members_trigger
    AFTER INSERT OR UPDATE OR DELETE ON organization_members
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

-- Update permissions
GRANT ALL ON audit_logs TO authenticated;
GRANT ALL ON audit_logs TO service_role;

-- Ensure RLS policy is correct
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS audit_logs_org_access_policy ON audit_logs;

CREATE POLICY audit_logs_org_access_policy ON audit_logs
    FOR ALL
    TO authenticated
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = COALESCE(
                current_setting('audit.user_id', true)::uuid,
                changed_by
            )
        )
    );

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_record_id ON audit_logs(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_changed_at ON audit_logs(changed_at);

COMMENT ON FUNCTION process_audit_log() IS 'Audit trigger function that logs changes with fallback to created_by for user identification'; 