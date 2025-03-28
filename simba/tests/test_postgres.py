import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()

import psycopg2
from psycopg2.extras import RealDictCursor

from simba.core.config import settings
from simba.database.postgres import PostgresDB

# Test direct connection to PostgreSQL
try:
    connection = psycopg2.connect(
        user=settings.postgres.user,
        password=settings.postgres.password,
        host=settings.postgres.host,
        port=settings.postgres.port,
        dbname=settings.postgres.db,
        sslmode="require",
    )
    print("Connection successful!")

    # Create a cursor to execute SQL queries
    cursor = connection.cursor()

    # Example query
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Current Time:", result)

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connection closed.")

except Exception as e:
    print(f"Failed to connect: {e}")


# Test using the PostgresDB class
try:
    print("\nTesting PostgresDB class...")

    # Test connection
    if PostgresDB.test_connection():
        print("PostgresDB connection test successful!")

        # Run a test query
        current_time = PostgresDB.fetch_one("SELECT NOW() as time")
        print(f"Current time from PostgresDB: {current_time['time']}")
    else:
        print("PostgresDB connection test failed!")

except Exception as e:
    print(f"PostgresDB test error: {e}")
