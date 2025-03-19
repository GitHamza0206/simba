import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from fastapi import HTTPException, status
from contextlib import contextmanager

from simba.core.config import settings

logger = logging.getLogger(__name__)

class PostgresDB:
    """PostgreSQL database access with connection pooling."""
    
    # Connection pool singleton
    _pool = None
    
    @classmethod
    def _get_pool(cls):
        """Get or create the connection pool.
        
        Returns:
            ThreadedConnectionPool: Database connection pool
        """
        if cls._pool is None:
            try:
                # Create a connection pool with reasonable defaults
                cls._pool = ThreadedConnectionPool(
                    minconn=3,
                    maxconn=10,
                    user=settings.postgres.user,
                    password=settings.postgres.password,
                    host=settings.postgres.host,
                    port=settings.postgres.port,
                    dbname=settings.postgres.db,
                    sslmode='require'
                )
                logger.info("Created PostgreSQL connection pool")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to connect to database"
                )
        return cls._pool
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """Get a connection from the pool and return it when done.
        
        Yields:
            Connection: Database connection
        """
        pool = cls._get_pool()
        conn = None
        try:
            conn = pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
        finally:
            if conn:
                pool.putconn(conn)
    
    @classmethod
    def execute_query(cls, query, params=None):
        """Run an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            int: Number of rows affected
        """
        with cls.get_connection() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    rowcount = cursor.rowcount
                conn.commit()
                return rowcount
            except Exception as e:
                conn.rollback()
                logger.error(f"Query execution error: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database query failed"
                )
    
    @classmethod
    def fetch_all(cls, query, params=None):
        """Run a SELECT query and return all results.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            list: Query results as dictionaries
        """
        with cls.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return [dict(row) for row in results]
    
    @classmethod
    def fetch_one(cls, query, params=None):
        """Run a SELECT query and return one result.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            dict: Query result as dictionary or None
        """
        with cls.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()
                return dict(row) if row else None
    
    @classmethod
    def test_connection(cls):
        """Test if database connection works.
        
        Returns:
            bool: True if connection successful
        """
        try:
            with cls.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
            
    @classmethod
    def close_pool(cls):
        """Close all connections in the pool."""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            logger.info("Closed PostgreSQL connection pool") 