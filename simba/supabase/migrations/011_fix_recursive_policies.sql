-- =============================================================
-- Section 11: Fix Recursive Policies
-- =============================================================

-- Drop existing policies
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
    EXISTS (
        SELECT 1 
        FROM organization_members 
        WHERE organization_id = organizations.id
        AND user_id = auth.uid()
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
    EXISTS (
        SELECT 1 
        FROM organization_members 
        WHERE organization_id = organizations.id
        AND user_id = auth.uid()
        AND role IN ('owner', 'admin')
    )
);

CREATE POLICY "org_delete_policy" ON organizations
FOR DELETE 
USING (
    EXISTS (
        SELECT 1 
        FROM organization_members 
        WHERE organization_id = organizations.id
        AND user_id = auth.uid()
        AND role = 'owner'
    )
);

-- Organization members table policies
CREATE POLICY "org_member_select_policy" ON organization_members
FOR SELECT 
USING (
    -- Users can see members of organizations they belong to
    EXISTS (
        SELECT 1 
        FROM organization_members AS om
        WHERE om.organization_id = organization_members.organization_id
        AND om.user_id = auth.uid()
    )
);

CREATE POLICY "org_member_insert_policy" ON organization_members
FOR INSERT 
WITH CHECK (
    -- Only owners/admins can add members
    EXISTS (
        SELECT 1 
        FROM organization_members AS om
        WHERE om.organization_id = organization_members.organization_id
        AND om.user_id = auth.uid()
        AND om.role IN ('owner', 'admin')
    )
);

CREATE POLICY "org_member_update_policy" ON organization_members
FOR UPDATE 
USING (
    -- Only owners can update member details
    EXISTS (
        SELECT 1 
        FROM organization_members AS om
        WHERE om.organization_id = organization_members.organization_id
        AND om.user_id = auth.uid()
        AND om.role = 'owner'
    )
);

CREATE POLICY "org_member_delete_policy" ON organization_members
FOR DELETE 
USING (
    -- Owners can remove any member, users can remove themselves
    (
        EXISTS (
            SELECT 1 
            FROM organization_members AS om
            WHERE om.organization_id = organization_members.organization_id
            AND om.user_id = auth.uid()
            AND om.role = 'owner'
        )
    ) OR auth.uid() = user_id
);

DO $$ 
BEGIN
    RAISE NOTICE 'Organization RLS policies have been updated to fix recursion issues';
END $$; 