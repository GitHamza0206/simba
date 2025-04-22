# Setting up Roles Tables in Supabase

This document explains how to set up the role management tables in your Supabase database.

## Overview

The role management system consists of four main tables:

1. `roles` - Defines the available roles in the system
2. `permissions` - Defines individual permissions
3. `role_permissions` - Maps permissions to roles (many-to-many)
4. `user_roles` - Maps roles to users (many-to-many)

## Setup Options

There are multiple ways to apply the migrations:

### Option 1: Using the Supabase SQL Editor

1. Log into your [Supabase Dashboard](https://app.supabase.io/)
2. Select your project
3. Go to the SQL Editor
4. Copy the contents of the following files and execute them in order:
   - `simba/database/migrations/001_create_roles_tables.sql`
   - `simba/database/migrations/002_execute_roles_setup.sql`

### Option 2: Using the Migration Script

We've provided a Python script to automatically apply migrations:

1. Install required dependencies:
   ```bash
   pip install asyncpg python-dotenv
   ```

2. Set up environment variables by creating a `.env` file at the project root:
   ```
   SUPABASE_DB_URL=postgres://postgres:your-password@db.your-project-ref.supabase.co:5432/postgres
   # Or set individual components:
   # SUPABASE_DB_HOST=db.your-project-ref.supabase.co
   # SUPABASE_DB_PORT=5432
   # SUPABASE_DB_NAME=postgres
   # SUPABASE_DB_USER=postgres
   # SUPABASE_DB_PASSWORD=your-password
   ```

3. Run the migration script:
   ```bash
   python scripts/apply_migrations.py
   ```

   To apply a specific migration file:
   ```bash
   python scripts/apply_migrations.py --migration-file 001_create_roles_tables.sql
   ```

### Option 3: Using the Supabase CLI

If you have the [Supabase CLI](https://supabase.com/docs/guides/cli) installed:

1. Set up your Supabase project locally
2. Copy the migration files to the `supabase/migrations` directory
3. Run migrations with:
   ```bash
   supabase db push
   ```

## Creating an Admin User

To assign the admin role to a user:

1. Create a regular user through your application signup process
2. Use the SQL editor to assign the admin role:

```sql
INSERT INTO user_roles (user_id, role_id)
SELECT 
  auth.users.id, 
  roles.id
FROM 
  auth.users, 
  roles
WHERE 
  auth.users.email = 'your-admin-email@example.com'
  AND roles.name = 'admin'
ON CONFLICT (user_id, role_id) DO NOTHING;
```

## Verifying the Setup

Test if the roles setup is working by executing:

```sql
-- Replace with an actual user ID
SELECT user_has_role('user-uuid-here', 'admin');

-- Check what roles a user has
SELECT r.name
FROM roles r
JOIN user_roles ur ON r.id = ur.role_id
WHERE ur.user_id = 'user-uuid-here';
```

## Troubleshooting

If you encounter any issues:

1. Check that the `auth.users` table exists and has the expected structure
2. Verify that the RLS policies are correctly applied
3. Make sure your API calls include the correct authentication headers 