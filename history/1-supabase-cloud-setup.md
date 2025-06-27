# Supabase Cloud Connection Tutorial

## Overview
This tutorial walks you through connecting your Simba application to Supabase cloud from scratch. The integration provides authentication, database storage, and file storage capabilities using Supabase's managed services.

## Prerequisites
- A Supabase account (sign up at [supabase.com](https://supabase.com))
- Access to the Simba codebase
- Python 3.11+ installed
- Basic understanding of environment variables

## Step 1: Create a Supabase Project

1. **Sign in to Supabase Dashboard**
   - Go to [app.supabase.com](https://app.supabase.com)
   - Sign in or create a new account

2. **Create a New Project**
   - Click "New Project"
   - Choose your organization
   - Enter project name (e.g., "simba-production")
   - Set a strong database password
   - Select your region (choose closest to your users)
   - Click "Create new project"

3. **Wait for Setup**
   - Project creation takes 2-3 minutes
   - You'll get a project URL and API keys once ready

## Step 2: Gather Supabase Credentials

From your Supabase project dashboard, collect these values:

1. **Project URL**: Found in Settings → API
   - Format: `https://[project-ref].supabase.co`

2. **API Keys**: Found in Settings → API
   - `anon` key (public key)
   - `service_role` key (private key)

3. **Database Connection**: Found in Settings → Database
   - Connection string format: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`

4. **JWT Secret**: Found in Settings → API
   - Used for token verification

## Step 3: Environment Configuration

Create a `.env` file in your project root with the following variables:

```bash
# Supabase Configuration
SUPABASE_URL=https://[your-project-ref].supabase.co
SUPABASE_ANON_KEY=[your-anon-key]
SUPABASE_PUBLIC_KEY=[your-anon-key]  # Same as anon key
SERVICE_ROLE_KEY=[your-service-role-key]
JWT_SECRET=[your-jwt-secret]

# Database Configuration (Supabase Postgres)
POSTGRES_HOST=db.[your-project-ref].supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[your-database-password]
POSTGRES_DB=postgres
POSTGRES_CONNECTION_STRING=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres

# Storage Configuration
SUPABASE_STORAGE_BUCKET=simba-bucket

# Redis Configuration (for local development)
REDIS_HOST=localhost
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# API Keys
OPENAI_API_KEY=[your-openai-api-key]
```

## Step 4: Database Setup and Migrations

The Simba application requires specific database schema and functions. Run the migrations in the correct order:

### Option 1: Using Supabase SQL Editor

1. **Access SQL Editor**
   - Go to your Supabase dashboard
   - Navigate to "SQL Editor"

2. **Run Migrations in Order**
   Execute these files sequentially from `simba/supabase/migrations/`:

   ```sql
   -- 1. Extensions and Global Functions
   -- Run: 001_extensions_global_functions.sql
   
   -- 2. Roles and Permissions
   -- Run: 002_roles_permissions.sql
   
   -- 3. Organizations
   -- Run: 003_organizations.sql
   
   -- 4. Documents
   -- Run: 004_documents.sql
   
   -- 5. Chunks and Embeddings
   -- Run: 005_chunks_embeddings.sql
   
   -- 6. API Keys
   -- Run: 006_api_keys.sql
   
   -- 7. Final Grants
   -- Run: 007_final_grants.sql
   
   -- 8. Additional migrations as needed
   -- Run remaining numbered files in order
   ```

### Option 2: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize Supabase in your project
supabase init

# Copy migration files to supabase/migrations/
cp simba/supabase/migrations/* supabase/migrations/

# Apply migrations
supabase db push --db-url "postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
```

## Step 5: Storage Bucket Setup

1. **Create Storage Bucket**
   - Go to Storage in Supabase dashboard
   - Click "Create bucket"
   - Name: `simba-bucket` (or as configured in your .env)
   - Set as Public or Private based on your needs

2. **Configure Bucket Policies**
   ```sql
   -- Allow authenticated users to upload files
   CREATE POLICY "Allow authenticated uploads" ON storage.objects
   FOR INSERT TO authenticated
   WITH CHECK (bucket_id = 'simba-bucket');
   
   -- Allow authenticated users to read files
   CREATE POLICY "Allow authenticated reads" ON storage.objects
   FOR SELECT TO authenticated
   USING (bucket_id = 'simba-bucket');
   ```

## Step 6: Update Configuration Files

### Update config.yaml

```yaml
# config.yaml
database:
  provider: "supabase"

storage:
  provider: "supabase"
  supabase_bucket: "simba-bucket"

supabase:
  url: "${SUPABASE_URL}"
  key: "${SUPABASE_ANON_KEY}"
  service_role_key: "${SERVICE_ROLE_KEY}"
  jwt_secret: "${JWT_SECRET}"

postgres:
  connection_string: "${POSTGRES_CONNECTION_STRING}"
```

## Step 7: Verify Connection

### Test Database Connection

Create a simple test script:

```python
# test_supabase.py
import os
from dotenv import load_dotenv
from simba.auth.supabase_client import get_supabase_client

load_dotenv()

def test_connection():
    try:
        client = get_supabase_client()
        
        # Test basic query
        result = client.table('roles').select('*').limit(1).execute()
        print("✅ Database connection successful")
        print(f"Sample data: {result.data}")
        
        # Test storage
        buckets = client.storage.list_buckets()
        print("✅ Storage connection successful")
        print(f"Available buckets: {[b.name for b in buckets]}")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")

if __name__ == "__main__":
    test_connection()
```

### Run the Test

```bash
python test_supabase.py
```

## Step 8: Initialize Admin User

After successful connection, create an admin user:

1. **Sign up through your app** to create a user account

2. **Assign admin role** via SQL Editor:
   ```sql
   -- Find your user ID
   SELECT id, email FROM auth.users WHERE email = 'your-email@example.com';
   
   -- Assign admin role (replace with actual user ID)
   INSERT INTO user_roles (user_id, role_id)
   SELECT '[user-uuid]', r.id
   FROM roles r
   WHERE r.name = 'admin'
   ON CONFLICT DO NOTHING;
   ```

## File Structure Reference

The Supabase integration involves these key files:

- `simba/auth/supabase_client.py` - Singleton client management and connection logic
- `simba/core/config.py` - Configuration settings for Supabase and Postgres
- `simba/storage/supabase_storage.py` - File storage operations using Supabase Storage
- `simba/supabase/migrations/` - Database schema migrations
- `simba/supabase/config.toml` - Local development configuration
- `docker/docker-compose.yml` - Environment variable mapping for containerized deployment

## Key Components

### SupabaseClientSingleton
- **Location**: `simba/auth/supabase_client.py:12-75`
- **Purpose**: Manages single Supabase client instance across the application
- **Key logic**: Handles credential validation, client initialization with timeout configuration

### SupabaseStorageProvider
- **Location**: `simba/storage/supabase_storage.py:15-84`
- **Purpose**: Implements file storage operations using Supabase Storage API
- **Key features**: Bucket management, file upload/download, local temp file handling

### Configuration Management
- **Location**: `simba/core/config.py:194-261`
- **Purpose**: Centralizes all Supabase-related configuration settings
- **Environment variables**: Maps all required environment variables for Supabase services

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check network connectivity
   - Verify project URL and region
   - Ensure firewall allows connections to Supabase

2. **Authentication Errors**
   - Verify API keys are correct and not expired
   - Check environment variable names match exactly
   - Ensure service role key has proper permissions

3. **Storage Issues**
   - Verify bucket exists and name matches configuration
   - Check RLS policies allow your operations
   - Ensure bucket is in the correct region

4. **Migration Failures**
   - Run migrations in the correct order
   - Check for existing schema conflicts
   - Verify database user has sufficient privileges

### Debug Mode

Enable debug logging in your application:

```python
import logging
logging.getLogger('simba.auth.supabase_client').setLevel(logging.DEBUG)
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use service role key** only for server-side operations
3. **Implement proper RLS policies** for data protection
4. **Rotate API keys** regularly
5. **Monitor usage** in Supabase dashboard
6. **Use environment-specific projects** (dev/staging/prod)

## Usage Integration

Once connected, the Supabase integration works seamlessly with other Simba components:

- **Authentication**: User management, session handling, and JWT verification
- **Database**: Document metadata, user roles, and application data storage
- **Storage**: File uploads, document storage, and asset management
- **Vector Store**: When using PostgreSQL with pgvector extension for embeddings

The connection enables full-stack functionality with managed infrastructure, making Simba production-ready with minimal setup complexity. 