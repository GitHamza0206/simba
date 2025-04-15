-- =============================================================
-- Section 3: Organizations & Organization Members
-- =============================================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer', 'none')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, user_id),
    UNIQUE (organization_id, email)
);

-- Indexes for organization_members
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_email ON organization_members(email);
CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON organization_members(organization_id);

-- Enable RLS and create policies for organizations
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_select_policy ON organizations 
    FOR SELECT 
    USING (
        id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY org_insert_policy ON organizations 
    FOR INSERT 
    WITH CHECK (created_by = auth.uid());

CREATE POLICY org_update_policy ON organizations 
    FOR UPDATE 
    USING (
        id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid() AND role = 'owner'
        )
    );

CREATE POLICY org_delete_policy ON organizations 
    FOR DELETE 
    USING (
        id IN (
            SELECT organization_id 
            FROM organization_members 
            WHERE user_id = auth.uid() AND role = 'owner'
        )
    );

-- Enable RLS and create policies for organization_members
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

-- FIX: Avoid recursive policies by using simpler direct conditions
-- Members can see their own membership records
CREATE POLICY org_members_select_own_policy ON organization_members 
    FOR SELECT 
    USING (user_id = auth.uid());

-- Members can see membership records for organizations they belong to
CREATE POLICY org_members_select_policy ON organization_members 
    FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 
            FROM organization_members om
            WHERE om.organization_id = organization_members.organization_id 
            AND om.user_id = auth.uid()
        )
    );

-- Only owners and admins can add members
CREATE POLICY org_members_insert_policy ON organization_members 
    FOR INSERT 
    WITH CHECK (
        (
            organization_id IN (
                SELECT om.organization_id 
                FROM organization_members om
                WHERE om.user_id = auth.uid() 
                AND om.role IN ('owner', 'admin')
            )
        ) 
        OR 
        (
            -- Allow users to insert themselves into organizations by invite
            user_id = auth.uid()
        )
    );

-- Only owners can update member roles
CREATE POLICY org_members_update_policy ON organization_members 
    FOR UPDATE 
    USING (
        EXISTS (
            SELECT 1 
            FROM organization_members om
            WHERE om.organization_id = organization_members.organization_id 
            AND om.user_id = auth.uid() 
            AND om.role = 'owner'
        )
    );

-- Only owners can remove members
CREATE POLICY org_members_delete_policy ON organization_members 
    FOR DELETE 
    USING (
        EXISTS (
            SELECT 1 
            FROM organization_members om
            WHERE om.organization_id = organization_members.organization_id 
            AND om.user_id = auth.uid() 
            AND om.role = 'owner'
        )
        -- Allow users to remove themselves from organizations
        OR auth.uid() = user_id
    ); 