-- Migration to create API keys table in Supabase
-- This table stores API keys for auth without username/password

-- Create the api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT NOT NULL UNIQUE,  -- Hashed API key value
    key_prefix TEXT NOT NULL,  -- First few characters of key for display/identification
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,  -- Virtual user association
    name TEXT NOT NULL,  -- User-friendly name for the API key
    roles JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Associated roles
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- Create a trigger to update the last_used column
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

-- Add RLS policies
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Create policies for API key access control
CREATE POLICY "API keys are only visible to their creator" ON api_keys
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can only create API keys for themselves" ON api_keys
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can only update their own API keys" ON api_keys
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can only delete their own API keys" ON api_keys
    FOR DELETE USING (auth.uid() = user_id);

-- Function to check if an API key exists and is valid
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