"""
Middleware components for the Simba FastAPI application.

This module provides middleware components used across the API,
including authentication, logging, and error handling.
"""

# Import middleware components
from simba.api.middleware.auth import (
    get_current_user,
    http_bearer as security,
    require_role,
    require_permission
) 