-- Grant permissions to authenticated role for api_keys table
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.api_keys TO authenticated; 