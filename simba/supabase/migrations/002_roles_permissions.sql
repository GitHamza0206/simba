-- =============================================================
-- Section 2: Roles & Permissions
-- =============================================================

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,          -- e.g., 'admin', 'user'
  description TEXT,                   -- Human-readable description
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,          -- e.g., 'users:read'
  description TEXT,                   -- Human-readable description
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Many-to-many mapping: Role-Permissions
CREATE TABLE IF NOT EXISTS role_permissions (
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

-- Many-to-many mapping: User-Roles
CREATE TABLE IF NOT EXISTS user_roles (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

-- Insert default roles
INSERT INTO roles (name, description)
VALUES 
  ('admin', 'Full system access with all permissions'),
  ('user', 'Regular user with limited access')
ON CONFLICT (name) DO NOTHING;

-- Insert default permissions
INSERT INTO permissions (name, description)
VALUES
  ('users:read',   'Can view user information'),
  ('users:write',  'Can modify user information'),
  ('users:delete', 'Can delete users'),
  ('roles:read',   'Can view roles'),
  ('roles:write',  'Can modify roles'),
  ('roles:delete', 'Can delete roles')
ON CONFLICT (name) DO NOTHING;

-- Assign all permissions to admin role
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Assign basic permissions to user role (only 'users:read')
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p
WHERE r.name = 'user' AND p.name IN ('users:read')
ON CONFLICT DO NOTHING;

-- Helper functions to check user roles and permissions
CREATE OR REPLACE FUNCTION user_has_role(user_uuid UUID, role_name TEXT)
RETURNS BOOLEAN AS $$
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

CREATE OR REPLACE FUNCTION user_has_permission(user_uuid UUID, permission_name TEXT)
RETURNS BOOLEAN AS $$
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

-- Enable RLS on roles-related tables and create policies
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE role_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admins can do everything with roles" ON roles
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view roles" ON roles
    FOR SELECT
    USING (true);

CREATE POLICY "Admins can do everything with permissions" ON permissions
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view permissions" ON permissions
    FOR SELECT
    USING (true);

CREATE POLICY "Admins can do everything with role_permissions" ON role_permissions
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view role_permissions" ON role_permissions
    FOR SELECT
    USING (true);

CREATE POLICY "Admins can do everything with user_roles" ON user_roles
    FOR ALL
    USING (user_has_role(auth.uid(), 'admin'));

CREATE POLICY "Users can view their own roles" ON user_roles
    FOR SELECT
    USING (auth.uid() = user_id OR user_has_role(auth.uid(), 'admin')); 