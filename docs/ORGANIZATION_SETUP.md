# Organization Management Setup

This document provides instructions for setting up the organization management feature in Simba.

## Database Setup

The organization management feature requires two new tables in the database:
- `organizations` - Stores organization details
- `organization_members` - Stores organization membership information

Run the SQL migration script to create these tables:

```bash
# Execute the migration script using Supabase
supabase db execute simba/database/migrations/create_organization_tables.sql

# Or directly using psql (replace placeholders with actual values)
psql postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME -f simba/database/migrations/create_organization_tables.sql
```

## Backend Changes

The following backend files were added or modified to support organization management:

1. Added `simba/models/organization.py` - Contains Pydantic models for organizations and members
2. Added `simba/auth/organization_service.py` - Provides services for organization operations
3. Added `simba/api/organization_routes.py` - Defines FastAPI routes for organization endpoints
4. Modified `simba/__main__.py` - Includes the organization router in the main application

## Frontend Changes

The frontend needs to interact with the new organization API endpoints. The following files were added or modified:

1. Added `frontend/src/pages/OrganizationPage.tsx` - Organization management UI
2. Modified `frontend/src/App.tsx` - Added route for the organization page
3. Modified `frontend/src/components/layout/Sidebar.tsx` - Added organization link to the sidebar

## API Endpoints

The following API endpoints are available for organization management:

### Organizations

- `GET /organizations` - Get all organizations for the current user
- `POST /organizations` - Create a new organization
- `GET /organizations/{org_id}` - Get organization by ID

### Organization Members

- `GET /organizations/{org_id}/members` - Get organization members
- `POST /organizations/{org_id}/invite` - Invite a member to an organization
- `PUT /organizations/{org_id}/members/{member_id}` - Update a member's role
- `DELETE /organizations/{org_id}/members/{member_id}` - Remove a member from an organization

## Role-Based Access Control

The organization management feature implements the following role hierarchy:

1. **Owner** - Has full control over the organization, can invite/remove members and change roles
2. **Admin** - Can manage organization settings and invite members
3. **Member** - Has general access to organization resources
4. **Viewer** - Has read-only access to organization resources
5. **None** - Has no access to organization resources

## Testing

To test the organization management feature:

1. Log in as a user
2. Navigate to the Organizations page using the sidebar link
3. Create a new organization
4. Invite members using their email addresses
5. Assign roles to members
6. Test role permissions by logging in as different users 