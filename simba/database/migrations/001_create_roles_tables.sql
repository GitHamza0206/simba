-- Roles table
-- Stores the different roles available in the system
-- Each role represents a set of permissions granted to users
CREATE TABLE IF NOT EXISTS roles (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL, -- Unique role identifier (e.g., 'admin', 'user')
  description TEXT, -- Human-readable description of this role
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Permissions table
-- Stores individual permissions that can be granted to roles
CREATE TABLE IF NOT EXISTS permissions (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL, -- Unique permission identifier (e.g., 'users:read')
  description TEXT, -- Human-readable description of this permission
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Role-Permission mapping
-- Associates permissions with roles (many-to-many)
CREATE TABLE IF NOT EXISTS role_permissions (
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);

-- User-Role mapping
-- Associates roles with users (many-to-many)
CREATE TABLE IF NOT EXISTS user_roles (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);

-- Default roles
-- Only insert if not exists to allow customization
INSERT INTO roles (name, description)
VALUES 
  ('admin', 'Full system access with all permissions')
ON CONFLICT (name) DO NOTHING;

INSERT INTO roles (name, description)
VALUES 
  ('user', 'Regular user with limited access')
ON CONFLICT (name) DO NOTHING;

-- Default permissions
-- Only insert if not exists to allow customization
INSERT INTO permissions (name, description)
VALUES 
  ('users:read', 'Can view user information')
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description)
VALUES 
  ('users:write', 'Can modify user information')
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description)
VALUES 
  ('users:delete', 'Can delete users')
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description)
VALUES 
  ('roles:read', 'Can view roles')
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description)
VALUES 
  ('roles:write', 'Can modify roles')
ON CONFLICT (name) DO NOTHING;

INSERT INTO permissions (name, description)
VALUES 
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

-- Function to check if a user has a specific role
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

-- Function to check if a user has a specific permission
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

-- Function to update the updated_at timestamp automatically
-- Used by multiple tables throughout the schema
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql'; 