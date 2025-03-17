# Role Management System Setup

This document describes how to set up the role management system in your Supabase database.

## Overview

The role management system consists of four main tables:

1. `roles`: Defines different user roles (e.g., admin, user)
2. `permissions`: Defines individual permissions (e.g., users:read, users:write)
3. `role_permissions`: Maps which permissions belong to which roles
4. `user_roles`: Assigns roles to specific users

## Setup Instructions

### Option 1: Using Supabase SQL Editor

1. Log into your [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to the SQL Editor
4. Create a new query
5. Copy the entire contents of the `direct_sql_commands.sql` file into the SQL Editor
6. Run the query

### Option 2: Using the Provided SQL Script

1. Open the Supabase SQL Editor
2. Create a new query
3. Copy and paste the SQL commands from the `direct_sql_commands.sql` file
4. Run the query

## Assigning an Admin Role

To assign an admin role to a user, you need the user's UUID from the `auth.users` table:

```sql
-- Find a user by email
SELECT id FROM auth.users WHERE email = 'your.email@example.com';

-- Assign admin role to a user (replace with the actual UUID)
INSERT INTO user_roles (user_id, role_id)
SELECT 'user-uuid-here', r.id
FROM roles r
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;
```

## Verifying Setup

You can verify the setup by running these queries:

```sql
-- Check if a specific user has admin role
SELECT user_has_role('user-uuid-here', 'admin');

-- List all roles for a specific user
SELECT r.name AS role_name
FROM user_roles ur
JOIN roles r ON r.id = ur.role_id
WHERE ur.user_id = 'user-uuid-here';

-- List all permissions for a specific user
SELECT p.name AS permission_name
FROM user_roles ur
JOIN role_permissions rp ON rp.role_id = ur.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE ur.user_id = 'user-uuid-here';
```

## Using Role Verification in Your Application

The database functions `user_has_role` and `user_has_permission` can be used in Row Level Security policies and your application code to authorize actions.

Example in RLS policy:
```sql
CREATE POLICY "Only admins can delete" ON some_table
  FOR DELETE
  USING (user_has_role(auth.uid(), 'admin'));
```

## Troubleshooting

If you encounter issues:

1. Check that the tables were created successfully:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('roles', 'permissions', 'role_permissions', 'user_roles');
   ```

2. Verify that the default roles and permissions were inserted:
   ```sql
   SELECT * FROM roles;
   SELECT * FROM permissions;
   ```

3. Ensure Row Level Security is enabled on all tables:
   ```sql
   SELECT tablename, rowsecurity 
   FROM pg_tables 
   WHERE schemaname = 'public' 
   AND tablename IN ('roles', 'permissions', 'role_permissions', 'user_roles');
   ```

4. Check if the RLS policies were created:
   ```sql
   SELECT tablename, policyname 
   FROM pg_policies 
   WHERE schemaname = 'public' 
   AND tablename IN ('roles', 'permissions', 'role_permissions', 'user_roles');
   ``` 