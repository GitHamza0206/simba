-- This script ensures the roles tables are correctly configured in Supabase
-- It enables Row Level Security and sets up appropriate policies

-- Enable Row Level Security on roles tables
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for roles table
CREATE POLICY "Admins can do everything with roles" ON roles
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view roles" ON roles
    FOR SELECT
    USING (true);

-- Create RLS policies for permissions table
CREATE POLICY "Admins can do everything with permissions" ON permissions
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view permissions" ON permissions
    FOR SELECT
    USING (true);

-- Create RLS policies for role_permissions table
CREATE POLICY "Admins can do everything with role_permissions" ON role_permissions
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view role_permissions" ON role_permissions
    FOR SELECT
    USING (true);

-- Create RLS policies for user_roles table
CREATE POLICY "Admins can do everything with user_roles" ON user_roles
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view their own roles" ON user_roles
    FOR SELECT
    USING (auth.uid() = user_id OR user_has_role(auth.uid(), 'admin'));

-- Create a super admin user if needed (you can execute this manually with your admin email)
-- Replace 'admin@example.com' with your actual admin email
-- This part is commented out by default - uncomment and run manually when needed
/*
DO $$
DECLARE
    admin_role_id INTEGER;
    admin_user_id UUID;
BEGIN
    SELECT id INTO admin_role_id FROM roles WHERE name = 'admin';
    SELECT id INTO admin_user_id FROM auth.users WHERE email = 'admin@example.com';
    
    IF admin_user_id IS NOT NULL AND admin_role_id IS NOT NULL THEN
        INSERT INTO user_roles (user_id, role_id)
        VALUES (admin_user_id, admin_role_id)
        ON CONFLICT (user_id, role_id) DO NOTHING;
    END IF;
END
$$;
*/

-- Additional organization-specific roles if needed
-- Uncomment and modify as necessary
/*
INSERT INTO roles (name, description)
VALUES 
  ('org_admin', 'Organization administrator'),
  ('org_member', 'Organization member')
ON CONFLICT (name) DO NOTHING;
*/ 