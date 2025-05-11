-- =============================================================
-- Section 10: Fix Schema Permissions for Anon and Authenticated
-- =============================================================

-- Drop any conflicting permissions first to ensure clean state
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated CASCADE;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated CASCADE;
REVOKE ALL ON SCHEMA public FROM anon, authenticated CASCADE;

-- Grant schema usage to both anon and authenticated roles
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Grant table permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant read-only permissions to anon for public tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO anon;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE ON SEQUENCES TO authenticated, anon;

-- Verify specific permissions for organizations tables
GRANT SELECT, INSERT, UPDATE, DELETE ON organizations TO authenticated;
GRANT SELECT ON organizations TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON organization_members TO authenticated;
GRANT SELECT ON organization_members TO anon;

DO $$ 
BEGIN
    RAISE NOTICE 'Schema permissions have been fixed for anon and authenticated roles';
END $$; 