"""
Authentication module for the Simba application.

This module provides authentication functionality via Supabase,
including user management, token handling, and session management.
"""

from simba.auth.auth_service import AuthService
from simba.auth.supabase_client import get_supabase_client
