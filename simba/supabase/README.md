# Database Migrations

This directory contains SQL migration files for setting up the database schema using Supabase.

## Migration Order

The migrations are numbered to indicate the correct order for execution:

1. `001_extensions_global_functions.sql` - Sets up necessary extensions and global functions
2. `002_roles_permissions.sql` - Creates role and permission tables with default values
3. `003_organizations.sql` - Establishes organization and membership structure
4. `004_documents.sql` - Creates documents table for storing file metadata
5. `005_chunks_embeddings.sql` - Sets up vector storage for document chunks with embeddings
6. `006_api_keys.sql` - Implements API key management functionality
7. `007_final_grants.sql` - Grants necessary privileges and finalizes setup

## Running Migrations

To apply these migrations to your Supabase project, you can:

1. Run them through the Supabase dashboard SQL editor in the correct order
2. Use the Supabase CLI for deployment:
   ```bash
   supabase db push --db-url <your-db-url>
   ```

## Future Updates

When adding new features requiring schema changes:

1. Create a new numbered migration file (e.g., `008_new_feature.sql`)
2. Include only the changes needed for the new feature
3. Use ALTER TABLE statements rather than recreating existing tables
4. Apply the migration to your database

## Development Best Practices

- Always use IF NOT EXISTS in your CREATE statements
- Include indexes for fields that will be frequently queried
- Use comments to explain complex queries or constraints
- Test migrations thoroughly in a development environment before applying to production 