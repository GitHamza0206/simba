-- =============================================================
-- Section 12: Fix Recursion Properly with New Approach
-- =============================================================

-- Drop all existing policies to start fresh
DROP POLICY IF EXISTS org_select_policy ON organizations;
DROP POLICY IF EXISTS org_insert_policy ON organizations;
DROP POLICY IF EXISTS org_update_policy ON organizations;
DROP POLICY IF EXISTS org_delete_policy ON organizations;

DROP POLICY IF EXISTS org_member_select_policy ON organization_members;
DROP POLICY IF EXISTS org_member_insert_policy ON organization_members;
DROP POLICY IF EXISTS org_member_update_policy ON organization_members;
DROP POLICY IF EXISTS org_member_delete_policy ON organization_members;

DROP POLICY IF EXISTS org_members_select_own_policy ON organization_members;
DROP POLICY IF EXISTS org_members_select_policy ON organization_members;
DROP POLICY IF EXISTS org_members_insert_policy ON organization_members;
DROP POLICY IF EXISTS org_members_update_policy ON organization_members;
DROP POLICY IF EXISTS org_members_delete_policy ON organization_members;

-- ---------------------------------------------------------------
-- STEP 1: Create a helper function to check membership and role
-- This avoids recursion by using direct SQL rather than policies
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION is_org_member(
    org_id UUID, 
    user_id UUID, 
    required_roles TEXT[] DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    is_member BOOLEAN;
BEGIN
    IF required_roles IS NULL THEN
        -- Check if user is a member of the organization (any role)
        SELECT EXISTS (
            SELECT 1 FROM organization_members
            WHERE organization_id = org_id AND user_id = is_org_member.user_id
        ) INTO is_member;
    ELSE
        -- Check if user is a member with one of the specified roles
        SELECT EXISTS (
            SELECT 1 FROM organization_members
            WHERE organization_id = org_id
              AND user_id = is_org_member.user_id
              AND role = ANY(required_roles)
        ) INTO is_member;
    END IF;
    
    RETURN is_member;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ---------------------------------------------------------------
-- STEP 2: Create new non-recursive policies for organizations
-- ---------------------------------------------------------------
CREATE POLICY "org_select_policy" ON organizations
FOR SELECT 
USING (
    is_org_member(id, auth.uid())
);

CREATE POLICY "org_insert_policy" ON organizations
FOR INSERT 
WITH CHECK (
    auth.uid() = created_by
);

CREATE POLICY "org_update_policy" ON organizations
FOR UPDATE 
USING (
    is_org_member(id, auth.uid(), ARRAY['owner', 'admin'])
);

CREATE POLICY "org_delete_policy" ON organizations
FOR DELETE 
USING (
    is_org_member(id, auth.uid(), ARRAY['owner'])
);

-- ---------------------------------------------------------------
-- STEP 3: Create new non-recursive policies for organization_members
-- ---------------------------------------------------------------

-- Policy for the first member creation (owner of a new organization)
CREATE POLICY "org_members_first_owner" ON organization_members
FOR INSERT 
WITH CHECK (
    -- Allow the first owner to be created when organization is new
    -- This is needed for the first creation where there are no existing members
    role = 'owner' AND 
    user_id = auth.uid() AND
    NOT EXISTS (
        SELECT 1 FROM organization_members 
        WHERE organization_id = organization_members.organization_id
    )
);

-- Members can see their own membership
CREATE POLICY "org_members_see_own" ON organization_members
FOR SELECT 
USING (
    user_id = auth.uid()
);

-- Members can see all members of organizations they belong to
CREATE POLICY "org_members_see_others" ON organization_members
FOR SELECT 
USING (
    is_org_member(organization_id, auth.uid())
);

-- Owners and admins can invite new members
CREATE POLICY "org_members_invite" ON organization_members
FOR INSERT 
WITH CHECK (
    is_org_member(organization_id, auth.uid(), ARRAY['owner', 'admin'])
);

-- Only owners can update member roles
CREATE POLICY "org_members_update" ON organization_members
FOR UPDATE 
USING (
    is_org_member(organization_id, auth.uid(), ARRAY['owner'])
);

-- Owners can delete anyone, members can delete themselves
CREATE POLICY "org_members_delete" ON organization_members
FOR DELETE 
USING (
    is_org_member(organization_id, auth.uid(), ARRAY['owner']) OR 
    user_id = auth.uid()
);

-- ---------------------------------------------------------------
-- STEP 4: Verify fix with a notice
-- ---------------------------------------------------------------
DO $$ 
BEGIN
    RAISE NOTICE 'Organization RLS policies have been completely restructured to fix recursion issues';
END $$; 