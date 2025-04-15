-- =============================================================
-- Section 8: Add Service Role Grants
-- =============================================================

-- Grant privileges to service_role
GRANT USAGE ON SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;

DO $$ BEGIN
    RAISE NOTICE 'Service role grants added successfully';
END $$;
