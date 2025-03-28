"""
Middleware components for the Simba FastAPI application.

This module provides middleware components used across the API,
including authentication, logging, and error handling.
"""

# Import middleware components
from simba.api.middleware.auth import (
    get_current_user,
)
from simba.api.middleware.auth import http_bearer as security
from simba.api.middleware.auth import (
    require_permission,
    require_role,
)
