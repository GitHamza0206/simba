-- Enable audit functionality
CREATE EXTENSION IF NOT EXISTS plpgsql_check;

-- Create a function to set the audit user ID for the current session
CREATE OR REPLACE FUNCTION set_audit_user_id(user_id text)
RETURNS void AS $$
BEGIN
    -- Set at session level only
    PERFORM set_config('audit.user_id', user_id, false);
END;
$$ LANGUAGE plpgsql;

-- Update the audit trigger function to use session context
CREATE OR REPLACE FUNCTION process_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    org_id_val uuid;
    old_data_val jsonb;
    new_data_val jsonb;
    user_id_val text;
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

    -- Get the current user ID from session context
    BEGIN
        user_id_val := current_setting('audit.user_id', true);
        -- If no user_id set in session, use auth.uid() if available
        IF user_id_val IS NULL THEN
            BEGIN
                user_id_val := auth.uid()::text;
            EXCEPTION WHEN OTHERS THEN
                user_id_val := 'system';
            END;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        user_id_val := 'system';
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
        user_id_val,
        current_timestamp,
        TG_OP,
        old_data_val,
        new_data_val
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Make sure audit triggers are properly set
DROP TRIGGER IF EXISTS audit_organizations_trigger ON organizations;
DROP TRIGGER IF EXISTS audit_organization_members_trigger ON organization_members;

CREATE TRIGGER audit_organizations_trigger
    AFTER INSERT OR UPDATE OR DELETE ON organizations
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

CREATE TRIGGER audit_organization_members_trigger
    AFTER INSERT OR UPDATE OR DELETE ON organization_members
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

-- Grant necessary permissions
GRANT ALL ON audit_logs TO authenticated;
GRANT ALL ON audit_logs TO service_role;
GRANT EXECUTE ON FUNCTION set_audit_user_id TO authenticated;
GRANT EXECUTE ON FUNCTION set_audit_user_id TO service_role;

-- Add indexes for better audit log performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_record_id ON audit_logs(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_changed_at ON audit_logs(changed_at);

-- Add RLS policy for audit logs
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY audit_logs_org_access_policy ON audit_logs
    FOR ALL
    TO authenticated
    USING (
        organization_id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

COMMENT ON FUNCTION process_audit_log() IS 'Audit trigger function that logs changes to organizations and organization_members tables';
COMMENT ON FUNCTION set_audit_user_id IS 'Function to set the audit user ID for the current session'; 