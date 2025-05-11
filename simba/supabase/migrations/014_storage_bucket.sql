-- Create storage bucket for files
INSERT INTO storage.buckets (id, name, public)
VALUES ('simba-bucket', 'simba-bucket', false)
ON CONFLICT (id) DO NOTHING;

-- Enable RLS on storage.objects
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Create policies for storage.objects

-- Policy for reading files (authenticated users can read files in their organization)
CREATE POLICY "Allow organization members to read files"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'simba-bucket' AND
    EXISTS (
        SELECT 1 FROM organization_members om
        WHERE om.organization_id = (storage.objects.metadata->>'organization_id')::uuid
        AND om.user_id = auth.uid()
        AND om.role IN ('owner', 'admin', 'member', 'viewer')
    )
);

-- Policy for uploading files (authenticated users can upload to their organization)
CREATE POLICY "Allow organization members to upload files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'simba-bucket' AND
    EXISTS (
        SELECT 1 FROM organization_members om
        WHERE om.organization_id = (storage.objects.metadata->>'organization_id')::uuid
        AND om.user_id = auth.uid()
        AND om.role IN ('owner', 'admin', 'member')
    )
);

-- Policy for updating files (organization owners and admins can update files)
CREATE POLICY "Allow organization admins to update files"
ON storage.objects FOR UPDATE
TO authenticated
USING (
    bucket_id = 'simba-bucket' AND
    EXISTS (
        SELECT 1 FROM organization_members om
        WHERE om.organization_id = (storage.objects.metadata->>'organization_id')::uuid
        AND om.user_id = auth.uid()
        AND om.role IN ('owner', 'admin')
    )
)
WITH CHECK (
    bucket_id = 'simba-bucket' AND
    EXISTS (
        SELECT 1 FROM organization_members om
        WHERE om.organization_id = (storage.objects.metadata->>'organization_id')::uuid
        AND om.user_id = auth.uid()
        AND om.role IN ('owner', 'admin')
    )
);

-- Policy for deleting files (organization owners and admins can delete files)
CREATE POLICY "Allow organization admins to delete files"
ON storage.objects FOR DELETE
TO authenticated
USING (
    bucket_id = 'simba-bucket' AND
    EXISTS (
        SELECT 1 FROM organization_members om
        WHERE om.organization_id = (storage.objects.metadata->>'organization_id')::uuid
        AND om.user_id = auth.uid()
        AND om.role IN ('owner', 'admin')
    )
);

-- Grant necessary permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON storage.objects TO authenticated;
GRANT USAGE ON SCHEMA storage TO authenticated;

-- Create function to get file URL
CREATE OR REPLACE FUNCTION storage.get_file_url(bucket_id text, object_name text)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN storage.get_public_url(bucket_id, object_name);
END;
$$;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION storage.get_file_url TO authenticated; 