#!/usr/bin/env python3
"""
Script to apply database migrations to a Supabase database.
Usage:
    python apply_migrations.py [--migration-file filename]
"""

import argparse
import os
import sys
from pathlib import Path
import logging
import asyncio
import asyncpg
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database connection parameters from environment variables
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
SUPABASE_DB_HOST = os.getenv("SUPABASE_DB_HOST", "localhost")
SUPABASE_DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")
SUPABASE_DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
SUPABASE_DB_USER = os.getenv("SUPABASE_DB_USER", "postgres")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "postgres")

# Path to migrations directory
MIGRATIONS_DIR = Path(__file__).parent.parent / "simba" / "database" / "migrations"

async def get_db_connection():
    """Get a connection to the database."""
    try:
        # Use connection URL if provided, otherwise build from components
        if SUPABASE_DB_URL:
            conn = await asyncpg.connect(SUPABASE_DB_URL)
        else:
            conn = await asyncpg.connect(
                host=SUPABASE_DB_HOST,
                port=SUPABASE_DB_PORT,
                user=SUPABASE_DB_USER,
                password=SUPABASE_DB_PASSWORD,
                database=SUPABASE_DB_NAME,
            )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        sys.exit(1)

async def apply_migration_file(filename):
    """Apply a specific migration file."""
    file_path = MIGRATIONS_DIR / filename
    
    if not file_path.exists():
        logger.error(f"Migration file not found: {file_path}")
        return False
    
    logger.info(f"Applying migration: {filename}")
    
    # Read SQL content from file
    with open(file_path, "r") as f:
        sql_content = f.read()
    
    # Apply migration
    try:
        conn = await get_db_connection()
        try:
            # Start a transaction
            async with conn.transaction():
                await conn.execute(sql_content)
            
            logger.info(f"Successfully applied migration: {filename}")
            return True
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error applying migration {filename}: {str(e)}")
        return False

async def apply_all_migrations():
    """Apply all migration files in order."""
    success = True
    
    # Get all SQL migration files and sort them
    migration_files = sorted([f for f in MIGRATIONS_DIR.glob("*.sql")])
    
    for file_path in migration_files:
        result = await apply_migration_file(file_path.name)
        if not result:
            success = False
    
    return success

async def main():
    parser = argparse.ArgumentParser(description="Apply database migrations to Supabase")
    parser.add_argument("--migration-file", help="Specific migration file to apply")
    args = parser.parse_args()
    
    if args.migration_file:
        success = await apply_migration_file(args.migration_file)
    else:
        success = await apply_all_migrations()
    
    if success:
        logger.info("Migration(s) completed successfully")
    else:
        logger.error("Migration(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 