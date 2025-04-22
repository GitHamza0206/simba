# Role-Based Access Control (RBAC) in Simba

This document explains the Role-Based Access Control (RBAC) system implemented in Simba. This system allows for fine-grained permission control across the application.

## Overview

The RBAC system is built on these key concepts:

1. **Users**: Individuals who access the system
2. **Roles**: Named collections of permissions (e.g., "admin", "user")
3. **Permissions**: Specific actions that can be performed (e.g., "users:read", "roles:write")

## Database Schema

The RBAC system consists of four primary tables:

### `roles` Table

Stores the different roles available in the system.

```sql
CREATE TABLE roles (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### `permissions` Table

Stores individual permissions that can be granted to roles.

```sql
CREATE TABLE permissions (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### `role_permissions` Table

Links roles to permissions (many-to-many relationship).

```sql
CREATE TABLE role_permissions (
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
  PRIMARY KEY (role_id, permission_id)
);
```

### `user_roles` Table

Links users to roles (many-to-many relationship).

```sql
CREATE TABLE user_roles (
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, role_id)
);
```

## Default Roles and Permissions

The system comes with two predefined roles:

1. **admin**: Has all permissions
2. **user**: Has limited permissions (currently only "users:read")

The following permissions are predefined:

- `users:read`: Can view user information
- `users:write`: Can modify user information
- `users:delete`: Can delete users
- `roles:read`: Can view roles
- `roles:write`: Can modify roles
- `roles:delete`: Can delete roles

## API Endpoints

The following API endpoints are available for role management:

### Roles

- `GET /roles`: Get all roles (requires "roles:read" permission)
- `GET /roles/{role_id}`: Get a specific role (requires "roles:read" permission)
- `POST /roles`: Create a new role (requires "roles:write" permission)
- `PUT /roles/{role_id}`: Update a role (requires "roles:write" permission)
- `DELETE /roles/{role_id}`: Delete a role (requires "roles:delete" permission)

### Permissions

- `GET /roles/permissions`: Get all permissions (requires "roles:read" permission)
- `GET /roles/{role_id}/permissions`: Get permissions for a role (requires "roles:read" permission)

### User Roles

- `GET /roles/user/{user_id}`: Get roles for a user (user can see their own roles, others require "roles:read" permission)
- `POST /roles/user/{user_id}`: Assign a role to a user (requires "roles:write" permission)
- `DELETE /roles/user/{user_id}/{role_id}`: Remove a role from a user (requires "roles:write" permission)
- `GET /roles/user/{user_id}/permissions`: Get permissions for a user (user can see their own permissions, others require "roles:read" permission)

## Usage Examples

### Checking if a User Has a Role

```python
from simba.auth.role_service import RoleService

# Check if a user has a specific role
has_admin_role = await RoleService.has_role(user_id, "admin")
```

### Checking if a User Has a Permission

```python
from simba.auth.role_service import RoleService

# Check if a user has a specific permission
can_read_users = await RoleService.has_permission(user_id, "users:read")
```

### Protecting Routes with Role Middleware

```python
from fastapi import APIRouter, Depends
from simba.api.middleware.auth import require_role, require_permission

router = APIRouter()

@router.get("/admin-only")
async def admin_only(current_user: dict = Depends(require_role("admin"))):
    return {"message": "You are an admin!"}

@router.get("/users")
async def get_users(current_user: dict = Depends(require_permission("users:read"))):
    # Get users
    return {"message": "You can read users!"}
```

## Setup and Migration

To set up the RBAC schema in your database, run the provided setup script:

```bash
python -m simba.scripts.setup_rbac
```

This script will create the necessary tables, functions, and default roles and permissions.

## Extending the System

### Adding Custom Roles

```python
from simba.auth.role_service import RoleService

# Create a new role
editor_role = await RoleService.create_role(
    name="editor",
    description="Can edit content but not manage users"
)
```

### Adding Custom Permissions

You can add custom permissions directly in the database:

```sql
INSERT INTO permissions (name, description)
VALUES ('content:write', 'Can create and edit content');
```

Then associate them with roles:

```sql
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'editor' AND p.name = 'content:write';
```

## Security Considerations

- The RBAC system provides authorization, not authentication. Authentication is handled by Supabase.
- All roles and permissions are stored in the database and can be modified at runtime.
- When a user signs up, they are automatically assigned the "user" role.
- Users cannot assign themselves roles with higher privileges than they currently have.

## Troubleshooting

If you encounter issues with the RBAC system, check the following:

1. Ensure the user has the appropriate role or permission in the database
2. Verify that the role or permission exists in the database
3. Check the logs for any errors related to role checks

For more information, see the [API documentation](/api/roles) for the RBAC endpoints. 