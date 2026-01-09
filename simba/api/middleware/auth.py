"""Authentication middleware for multi-tenant API."""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from simba.models.base import get_db


class OrganizationContext:
    """Context object containing organization information."""

    def __init__(self, organization_id: str):
        self.organization_id = organization_id

    def __repr__(self) -> str:
        return f"<OrganizationContext(org_id={self.organization_id})>"


async def get_current_org(
    x_organization_id: str = Header(..., description="Organization ID"),
    db: Session = Depends(get_db),
) -> OrganizationContext:
    """
    Dependency to get the current organization from request headers.

    The organization ID is passed via X-Organization-Id header from the frontend.
    The session token is validated via cookies by Better Auth in the frontend.

    For now, we trust the organization ID from the header since:
    1. The frontend validates the session before making API calls
    2. The frontend only sends org IDs that the user is a member of

    In a production environment, you would want to validate that the user
    actually has access to this organization by checking the Better Auth
    session and member tables.
    """
    if not x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Organization ID is required",
        )

    # Validate that the organization exists in Better Auth tables
    # Better Auth creates these tables: organization, member, session, user
    result = db.execute(
        text("SELECT id FROM organization WHERE id = :org_id"),
        {"org_id": x_organization_id},
    )
    org = result.fetchone()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return OrganizationContext(organization_id=x_organization_id)


async def get_optional_org(
    x_organization_id: str | None = Header(None, description="Organization ID"),
    db: Session = Depends(get_db),
) -> OrganizationContext | None:
    """
    Optional organization dependency for endpoints that may work without org context.
    """
    if not x_organization_id:
        return None

    result = db.execute(
        text("SELECT id FROM organization WHERE id = :org_id"),
        {"org_id": x_organization_id},
    )
    org = result.fetchone()

    if not org:
        return None

    return OrganizationContext(organization_id=x_organization_id)
