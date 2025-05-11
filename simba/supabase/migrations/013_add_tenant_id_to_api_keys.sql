-- Add tenant_id column to api_keys table without foreign key
-- (we'll add constraints later when tenants table exists)
ALTER TABLE api_keys
ADD COLUMN tenant_id UUID;

-- Create index for faster tenant-based queries
CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);

-- Add a comment explaining the purpose
COMMENT ON COLUMN api_keys.tenant_id IS 'The tenant that this API key belongs to'; 