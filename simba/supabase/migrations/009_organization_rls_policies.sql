-- Enable Row Level Security
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to make the migration idempotent)
DROP POLICY IF EXISTS org_select_policy ON organizations;
DROP POLICY IF EXISTS org_insert_policy ON organizations;
DROP POLICY IF EXISTS org_update_policy ON organizations;
DROP POLICY IF EXISTS org_delete_policy ON organizations;

DROP POLICY IF EXISTS org_member_select_policy ON organization_members;
DROP POLICY IF EXISTS org_member_insert_policy ON organization_members;
DROP POLICY IF EXISTS org_member_update_policy ON organization_members;
DROP POLICY IF EXISTS org_member_delete_policy ON organization_members;

-- Organizations table policies
CREATE POLICY "org_select_policy" ON organizations
FOR SELECT 
USING (
    auth.uid() IN (
        SELECT user_id 
        FROM organization_members 
        WHERE organization_id = id
    )
);

CREATE POLICY "org_insert_policy" ON organizations
FOR INSERT 
WITH CHECK (
    auth.uid() = created_by
);

CREATE POLICY "org_update_policy" ON organizations
FOR UPDATE 
USING (
    auth.uid() IN (
        SELECT user_id 
        FROM organization_members 
        WHERE organization_id = id 
        AND role IN ('owner', 'admin')
    )
);

CREATE POLICY "org_delete_policy" ON organizations
FOR DELETE 
USING (
    auth.uid() IN (
        SELECT user_id 
        FROM organization_members 
        WHERE organization_id = id 
        AND role = 'owner'
    )
);

-- Organization members table policies
CREATE POLICY "org_member_select_policy" ON organization_members
FOR SELECT 
USING (
    auth.uid() IN (
        SELECT user_id 
        FROM organization_members 
        WHERE organization_id = organization_members.organization_id
    )
);

CREATE POLICY "org_member_insert_policy" ON organization_members
FOR INSERT 
WITH CHECK (
    auth.uid() IN (
        SELECT user_id 
        FROM organization_members 
        WHERE organization_id = organization_members.organization_id
        AND role IN ('owner', 'admin')
    )
);

CREATE POLICY "org_member_update_policy" ON organization_members
FOR UPDATE 
USING (
    auth.uid() IN (
        SELECT user_id 
        FROM organization_members 
        WHERE organization_id = organization_members.organization_id
        AND role = 'owner'
    )
);

CREATE POLICY "org_member_delete_policy" ON organization_members
FOR DELETE 
USING (
    auth.uid() IN (
        SELECT user_id 
        FROM organization_members 
        WHERE organization_id = organization_members.organization_id
        AND role = 'owner'
    )
    OR auth.uid() = user_id  -- Users can remove themselves from organizations
);

-- Force RLS to be enabled (prevents accidental disabling)
ALTER TABLE organizations FORCE ROW LEVEL SECURITY;
ALTER TABLE organization_members FORCE ROW LEVEL SECURITY;

-- Grant necessary permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON organizations TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON organization_members TO authenticated;

-- Grant all permissions to service role (bypasses RLS)
GRANT ALL ON organizations TO service_role;
GRANT ALL ON organization_members TO service_role; 