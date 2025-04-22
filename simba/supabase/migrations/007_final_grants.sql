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