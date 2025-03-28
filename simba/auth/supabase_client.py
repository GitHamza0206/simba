import logging
import os
from typing import Optional

from supabase import Client, create_client
from supabase.client import ClientOptions

from simba.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseClientSingleton:
    """Singleton class for Supabase client to ensure only one connection exists."""

    _instance: Optional[Client] = None

    @classmethod
    def get_instance(cls) -> Client:
        """Get or create the Supabase client instance.

        Returns:
            Client: Supabase client instance

        Raises:
            ValueError: If Supabase URL or key is missing
        """
        if cls._instance is None:
            # Get credentials from environment variables directly, which is the recommended approach
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_PUBLIC_KEY")

            # Fall back to settings if env vars are not available
            if not supabase_url:
                supabase_url = settings.supabase.url
            if not supabase_key:
                supabase_key = settings.supabase.key

            logger.debug(f"Supabase URL configured: {bool(supabase_url)}")
            logger.debug(f"Supabase Key configured: {bool(supabase_key)}")

            if not supabase_url or not supabase_key:
                logger.error("Missing Supabase credentials in configuration")
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in .env file or environment variables"
                )

            try:
                logger.info(f"Initializing Supabase client with URL: {supabase_url}")

                # Create client with timeout options
                cls._instance = create_client(
                    supabase_url,
                    supabase_key,
                    options=ClientOptions(
                        postgrest_client_timeout=10,
                        storage_client_timeout=10,
                    ),
                )

                logger.info("✅ Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                raise

        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the Supabase client instance (useful for testing)."""
        cls._instance = None


# Export a function to get the singleton instance for easy import
def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    return SupabaseClientSingleton.get_instance()
