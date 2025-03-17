#!/usr/bin/env python
"""
This script sets up the role-based access control (RBAC) schema in the Supabase database.
It creates the necessary tables, functions, and default roles and permissions.
"""

import os
import sys
import logging
import asyncio
import argparse
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from asyncpg.exceptions import DuplicateTableError

# Add the parent directory to the path so we can import simba modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simba.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def execute_sql_file(conn, file_path: str):
    """Execute SQL commands from a file.
    
    Args:
        conn: Database connection
        file_path: Path to SQL file
    """
    try:
        with open(file_path, "r") as f:
            sql = f.read()
        
        # Execute the SQL
        await conn.execute(sql)
        logger.info(f"Executed SQL file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error executing SQL file {file_path}: {str(e)}")
        return False

async def setup_rbac_schema():
    """Set up the RBAC schema in the database."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get connection string from settings
        connection_string = f"postgresql://{settings.supabase.db_user}:{settings.supabase.db_password}@{settings.supabase.db_host}:{settings.supabase.db_port}/{settings.supabase.db_name}"
        
        # Connect to the database
        logger.info("Connecting to database...")
        conn = await asyncpg.connect(connection_string)
        
        # Get migration files directory
        migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
        
        # Execute migration files
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            logger.info(f"Applying migration: {migration_file.name}")
            success = await execute_sql_file(conn, str(migration_file))
            if not success:
                logger.error(f"Failed to apply migration: {migration_file.name}")
                return False
        
        # Assign admin role to the first user (optional)
        # Uncomment and modify this code to assign the admin role to a specific user
        """
        admin_email = "admin@example.com"  # Replace with real admin email
        
        # Get user ID by email (if using Supabase auth)
        user_row = await conn.fetchrow(
            "SELECT id FROM auth.users WHERE email = $1", admin_email
        )
        
        if user_row:
            user_id = user_row["id"]
            # Get admin role ID
            role_row = await conn.fetchrow(
                "SELECT id FROM roles WHERE name = 'admin'"
            )
            
            if role_row:
                role_id = role_row["id"]
                # Assign admin role to user
                await conn.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                    user_id, role_id
                )
                logger.info(f"Assigned admin role to user: {admin_email}")
            else:
                logger.warning("Admin role not found")
        else:
            logger.warning(f"User with email {admin_email} not found")
        """
        
        # Close the connection
        await conn.close()
        
        logger.info("RBAC schema setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error setting up RBAC schema: {str(e)}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Set up RBAC schema in the database")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without actually doing it")
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("Dry run mode. Would execute SQL files in:")
        migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
        for migration_file in sorted(migrations_dir.glob("*.sql")):
            logger.info(f"- {migration_file}")
        return 0
    
    # Run the async function
    success = asyncio.run(setup_rbac_schema())
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 