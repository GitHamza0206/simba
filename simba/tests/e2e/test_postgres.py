# import os
# import pytest
# from unittest.mock import MagicMock, patch
# from datetime import datetime
# import logging
# from typing import Dict, List, Any, Tuple
# from dotenv import load_dotenv

# # Configure logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# # Load environment variables
# load_dotenv()

# import psycopg2
# from psycopg2.extras import RealDictCursor

# from simba.database.postgres import PostgresDB
# from simba.core.config import settings

# @pytest.mark.e2e
# def test_postgres_direct_connection():
#     """
#     E2E: Test direct connection to PostgreSQL using psycopg2.
#     """
#     try:
#         connection = psycopg2.connect(
#             user=settings.postgres.user,
#             password=settings.postgres.password,
#             host=settings.postgres.host,
#             port=settings.postgres.port,
#             dbname=settings.postgres.db,
#             sslmode='disable'
#         )
#         cursor = connection.cursor()
#         cursor.execute("SELECT NOW();")
#         result = cursor.fetchone()
#         assert result is not None, "No result returned from SELECT NOW()"
#         cursor.close()
#         connection.close()
#     except Exception as e:
#         pytest.fail(f"Failed to connect to PostgreSQL directly: {e}")

# @pytest.mark.e2e
# def test_postgresdb_class_connection():
#     """
#     E2E: Test connection using the PostgresDB class.
#     """
#     try:
#         db = PostgresDB()
#         current_time = db.fetch_one("SELECT NOW() as time")
#         assert current_time is not None and 'time' in current_time, "No time returned from PostgresDB.fetch_one()"
#     except Exception as e:
#         pytest.fail(f"PostgresDB class test error: {e}")
    