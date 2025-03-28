"""Database module for direct PostgreSQL access and operations.

This module provides database connectivity and operations for the application,
with direct PostgreSQL access through connection pooling.
"""

from simba.database.postgres import PostgresDB

__all__ = ['PostgresDB'] 