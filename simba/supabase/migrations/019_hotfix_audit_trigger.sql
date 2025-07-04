-- This script fixes a bug in the audit trigger that caused an error when inserting into organization_members.
-- The process_audit_log function is updated to handle tables without a 'created_by' column.

-- Drop triggers and function to ensure a clean re-creation.
DROP TRIGGER IF EXISTS audit_organizations_trigger ON organizations CASCADE;
DROP TRIGGER IF EXISTS audit_organization_members_trigger ON organization_members CASCADE;
DROP FUNCTION IF EXISTS process_audit_log() CASCADE;

-- Recreate the function with improved logic to find the user ID.
CREATE OR REPLACE FUNCTION process_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    org_id_val uuid;
    old_data_val jsonb;
    new_data_val jsonb;
    current_user_id uuid;
BEGIN
    -- Get organization_id from the record
    IF TG_TABLE_NAME = 'organizations' THEN
        org_id_val := COALESCE(NEW.id, OLD.id);
    ELSE
        org_id_val := COALESCE(NEW.organization_id, OLD.organization_id);
    END IF;

    -- Convert old and new data to JSONB
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        old_data_val := to_jsonb(OLD);
    END IF;
    IF TG_OP IN ('UPDATE', 'INSERT') THEN
        new_data_val := to_jsonb(NEW);
    END IF;

    -- Try to get user_id from session setting first
    BEGIN
        current_user_id := current_setting('audit.user_id', true)::uuid;
    EXCEPTION WHEN OTHERS THEN
        current_user_id := NULL;
    END;

    -- If no session user_id, fallback for INSERT operations
    IF current_user_id IS NULL AND TG_OP = 'INSERT' THEN
        -- Check for 'created_by' field
        IF jsonb_path_exists(new_data_val, '$.created_by') AND new_data_val->>'created_by' IS NOT NULL THEN
            current_user_id := (new_data_val->>'created_by')::uuid;
        -- Check for 'user_id' field as another fallback
        ELSIF jsonb_path_exists(new_data_val, '$.user_id') AND new_data_val->>'user_id' IS NOT NULL THEN
            current_user_id := (new_data_val->>'user_id')::uuid;
        END IF;
    END IF;

    -- If user_id is still not found, we cannot proceed with logging.
    IF current_user_id IS NULL THEN
        RAISE EXCEPTION 'Audit log error: User ID could not be determined for operation % on table %', TG_OP, TG_TABLE_NAME;
    END IF;

    -- Insert into audit_logs
    INSERT INTO audit_logs (id, organization_id, table_name, record_id, changed_by, changed_at, operation, old_data, new_data)
    VALUES (
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

-- Recreate triggers on the tables
CREATE TRIGGER audit_organizations_trigger
    AFTER INSERT OR UPDATE OR DELETE ON organizations
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

CREATE TRIGGER audit_organization_members_trigger
    AFTER INSERT OR UPDATE OR DELETE ON organization_members
    FOR EACH ROW EXECUTE FUNCTION process_audit_log();

COMMENT ON FUNCTION process_audit_log() IS 'Audit trigger function that logs changes. It dynamically checks for created_by or user_id for user identification during inserts if a session user_id is not available.'; 