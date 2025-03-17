-- SQL commands to directly run in the Supabase SQL Editor
-- These commands will check if tables exist and create them if needed

-- Check if roles table exists and create if not
CREATE TABLE IF NOT EXISTS roles (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Check if permissions table exists and create if not
CREATE TABLE IF NOT EXISTS permissions (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Check if role_permissions table exists and create if not
CREATE TABLE IF NOT EXISTS role_permissions (
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

-- Check if user_roles table exists and create if not
CREATE TABLE IF NOT EXISTS user_roles (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

-- Insert default roles if they don't exist
INSERT INTO roles (name, description)
VALUES 
  ('admin', 'Full system access with all permissions'),
  ('user', 'Regular user with limited access')
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions if they don't exist
INSERT INTO permissions (name, description)
VALUES 
  ('users:read', 'Can view user information'),
  ('users:write', 'Can modify user information'),
  ('users:delete', 'Can delete users'),
  ('roles:read', 'Can view roles'),
  ('roles:write', 'Can modify roles'),
  ('roles:delete', 'Can delete roles')
ON CONFLICT (name) DO NOTHING;

-- Assign all permissions to admin role
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p
WHERE r.name = 'admin' 
ON CONFLICT DO NOTHING;

-- Assign basic permissions to user role
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p
WHERE r.name = 'user' AND p.name IN ('users:read')
ON CONFLICT DO NOTHING;

-- Create user_has_role function if it doesn't exist
CREATE OR REPLACE FUNCTION user_has_role(
  user_uuid UUID,
  role_name TEXT
) RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM user_roles ur
    JOIN roles r ON r.id = ur.role_id
    WHERE ur.user_id = user_uuid
    AND r.name = role_name
  );
END;
$$ LANGUAGE plpgsql;

-- Create user_has_permission function if it doesn't exist
CREATE OR REPLACE FUNCTION user_has_permission(
  user_uuid UUID,
  permission_name TEXT
) RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM user_roles ur
    JOIN role_permissions rp ON rp.role_id = ur.role_id
    JOIN permissions p ON p.id = rp.permission_id
    WHERE ur.user_id = user_uuid
    AND p.name = permission_name
  );
END;
$$ LANGUAGE plpgsql;

-- Enable Row Level Security on the tables
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for roles table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'roles' AND policyname = 'Admins can do everything with roles'
  ) THEN
    CREATE POLICY "Admins can do everything with roles" ON roles
      FOR ALL
      USING (user_has_role(auth.uid(), 'admin'));
  END IF;
  
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'roles' AND policyname = 'Users can view roles'
  ) THEN
    CREATE POLICY "Users can view roles" ON roles
      FOR SELECT
      USING (true);
  END IF;
END;
$$;

-- Create RLS policies for permissions table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'permissions' AND policyname = 'Admins can do everything with permissions'
  ) THEN
    CREATE POLICY "Admins can do everything with permissions" ON permissions
      FOR ALL
      USING (user_has_role(auth.uid(), 'admin'));
  END IF;
  
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'permissions' AND policyname = 'Users can view permissions'
  ) THEN
    CREATE POLICY "Users can view permissions" ON permissions
      FOR SELECT
      USING (true);
  END IF;
END;
$$;

-- Create RLS policies for role_permissions table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'role_permissions' AND policyname = 'Admins can do everything with role_permissions'
  ) THEN
    CREATE POLICY "Admins can do everything with role_permissions" ON role_permissions
      FOR ALL
      USING (user_has_role(auth.uid(), 'admin'));
  END IF;
  
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'role_permissions' AND policyname = 'Users can view role_permissions'
  ) THEN
    CREATE POLICY "Users can view role_permissions" ON role_permissions
      FOR SELECT
      USING (true);
  END IF;
END;
$$;

-- Create RLS policies for user_roles table
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'user_roles' AND policyname = 'Admins can do everything with user_roles'
  ) THEN
    CREATE POLICY "Admins can do everything with user_roles" ON user_roles
      FOR ALL
      USING (user_has_role(auth.uid(), 'admin'));
  END IF;
  
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'user_roles' AND policyname = 'Users can view their own roles'
  ) THEN
    CREATE POLICY "Users can view their own roles" ON user_roles
      FOR SELECT
      USING (auth.uid() = user_id OR user_has_role(auth.uid(), 'admin'));
  END IF;
END;
$$;

-- Verify setup by showing tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('roles', 'permissions', 'role_permissions', 'user_roles');

-- Show existing roles
SELECT * FROM roles;

-- Show existing permissions
SELECT * FROM permissions; 