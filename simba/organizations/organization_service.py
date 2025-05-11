import logging
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, text

from simba.database.postgres import PostgresDB, Base
from simba.models.organization import Organization, OrganizationCreate, OrganizationMember, OrganizationMemberInvite, OrganizationMemberUpdate

logger = logging.getLogger(__name__)

class SQLOrganization(Base):
    """SQLAlchemy model for organizations table"""
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False)
    
    # Add relationship to members
    members = relationship("SQLOrganizationMember", back_populates="organization", cascade="all, delete-orphan")

class SQLOrganizationMember(Base):
    """SQLAlchemy model for organization_members table"""
    __tablename__ = "organization_members"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    user_id = Column(String, nullable=True)  # Nullable for pending invites
    email = Column(String, nullable=False)  # Required for all members
    role = Column(String, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Add relationship to organization
    organization = relationship("SQLOrganization", back_populates="members")

class OrganizationService:
    def __init__(self):
        self.db = PostgresDB()
        self._Session = self.db._Session

    def _get_session(self) -> Session:
        return self._Session()

    def _set_audit_user(self, session: Session, user_id: str):
        """Set the user_id in session context for audit logging"""
        session.execute(text("SET LOCAL audit.user_id = :user_id"), {"user_id": user_id})

    async def get_organizations(self, user_id: str) -> List[Organization]:
        try:
            session = self._get_session()
            try:
                self._set_audit_user(session, user_id)
                # Query organizations where user is a member
                orgs = session.query(SQLOrganization)\
                    .join(SQLOrganizationMember)\
                    .filter(SQLOrganizationMember.user_id == user_id)\
                    .all()
                
                return [
                    Organization(
                        id=str(org.id),
                        name=org.name,
                        created_at=org.created_at,
                        created_by=str(org.created_by)
                    ) for org in orgs
                ]
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get organizations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve organizations: {str(e)}"
            )

    async def create_organization(self, organization: OrganizationCreate, user_id: str) -> Organization:
        try:
            session = self._get_session()
            try:
                self._set_audit_user(session, user_id)
                
                # Get user's email
                user_email = session.execute(
                    text("SELECT email FROM auth.users WHERE id = :user_id"),
                    {"user_id": user_id}
                ).scalar()
                
                if not user_email:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                # Create organization
                org_id = str(uuid4())
                new_org = SQLOrganization(
                    id=org_id,
                    name=organization.name,
                    created_by=user_id
                )
                session.add(new_org)
                
                # Add owner member
                member_id = str(uuid4())
                new_member = SQLOrganizationMember(
                    id=member_id,
                    organization_id=org_id,
                    user_id=user_id,
                    email=user_email,
                    role='owner'
                )
                session.add(new_member)
                
                session.commit()
                
                return Organization(
                    id=str(new_org.id),
                    name=new_org.name,
                    created_at=new_org.created_at,
                    created_by=str(new_org.created_by)
                )
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to create organization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization"
            )

    async def get_organization(self, org_id: str, user_id: str) -> Organization:
        try:
            session = self._get_session()
            try:
                self._set_audit_user(session, user_id)
                # Check if user is member
                member = session.query(SQLOrganizationMember)\
                    .filter(
                        SQLOrganizationMember.organization_id == org_id,
                        SQLOrganizationMember.user_id == user_id
                    ).first()
                
                if not member:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not a member of this organization"
                    )
                
                org = session.query(SQLOrganization)\
                    .filter(SQLOrganization.id == org_id)\
                    .first()
                
                if not org:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization not found"
                    )
                
                return Organization(
                    id=str(org.id),
                    name=org.name,
                    created_at=org.created_at,
                    created_by=str(org.created_by)
                )
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get organization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organization"
            )

    async def get_organization_members(self, org_id: str, user_id: str) -> List[OrganizationMember]:
        try:
            session = self._get_session()
            try:
                self._set_audit_user(session, user_id)
                # Check if user is member
                is_member = session.query(SQLOrganizationMember)\
                    .filter(
                        SQLOrganizationMember.organization_id == org_id,
                        SQLOrganizationMember.user_id == user_id
                    ).first()
                
                if not is_member:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not a member of this organization"
                    )
                
                members = session.query(SQLOrganizationMember)\
                    .filter(SQLOrganizationMember.organization_id == org_id)\
                    .all()
                
                return [
                    OrganizationMember(
                        id=str(member.id),
                        organization_id=str(member.organization_id),
                        user_id=str(member.user_id) if member.user_id else None,
                        email=member.email,
                        role=member.role,
                        joined_at=member.joined_at
                    ) for member in members
                ]
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get organization members: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organization members"
            )

    async def invite_member(self, org_id: str, invite: OrganizationMemberInvite, user_id: str) -> OrganizationMember:
        try:
            session = self._get_session()
            try:
                self._set_audit_user(session, user_id)
                # Check user permissions
                member = session.query(SQLOrganizationMember)\
                    .filter(
                        SQLOrganizationMember.organization_id == org_id,
                        SQLOrganizationMember.user_id == user_id
                    ).first()
                
                if not member or member.role not in ['owner', 'admin']:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You do not have permission to invite members"
                    )
                
                # Check if email already exists
                existing = session.query(SQLOrganizationMember)\
                    .filter(
                        SQLOrganizationMember.organization_id == org_id,
                        SQLOrganizationMember.email == invite.email
                    ).first()
                
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This email is already a member of the organization"
                    )
                
                # Create invitation
                member_id = str(uuid4())
                new_member = SQLOrganizationMember(
                    id=member_id,
                    organization_id=org_id,
                    email=invite.email,
                    role=invite.role
                )
                session.add(new_member)
                session.commit()
                
                return OrganizationMember(
                    id=str(new_member.id),
                    organization_id=str(new_member.organization_id),
                    user_id=None,  # For invitations, user_id is None
                    email=new_member.email,
                    role=new_member.role,
                    joined_at=new_member.joined_at
                )
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to invite member: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to invite member"
            )

    async def update_member_role(self, org_id: str, member_id: str, update: OrganizationMemberUpdate, user_id: str) -> OrganizationMember:
        try:
            session = self._get_session()
            try:
                self._set_audit_user(session, user_id)
                # Check if current user is owner
                current_member = session.query(SQLOrganizationMember)\
                    .filter(
                        SQLOrganizationMember.organization_id == org_id,
                        SQLOrganizationMember.user_id == user_id
                    ).first()
                
                if not current_member or current_member.role != 'owner':
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only owners can modify member roles"
                    )
                
                # Get member to update
                member = session.query(SQLOrganizationMember)\
                    .filter(
                        SQLOrganizationMember.id == member_id,
                        SQLOrganizationMember.organization_id == org_id
                    ).first()
                
                if not member:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Target member not found"
                    )
                
                # Check owner count if changing owner role
                if member.role == 'owner' and update.role != 'owner':
                    owners_count = session.query(SQLOrganizationMember)\
                        .filter(
                            SQLOrganizationMember.organization_id == org_id,
                            SQLOrganizationMember.role == 'owner'
                        ).count()
                    
                    if owners_count <= 1:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot change the role of the only owner"
                        )
                
                # Update role
                member.role = update.role
                session.commit()
                
                return OrganizationMember(
                    id=str(member.id),
                    organization_id=str(member.organization_id),
                    user_id=str(member.user_id) if member.user_id else None,
                    email=member.email,
                    role=member.role,
                    joined_at=member.joined_at
                )
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update member role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update member role"
            )

    async def remove_member(self, org_id: str, member_id: str, user_id: str):
        try:
            session = self._get_session()
            try:
                self._set_audit_user(session, user_id)
                # Check if current user is owner
                current_member = session.query(SQLOrganizationMember)\
                    .filter(
                        SQLOrganizationMember.organization_id == org_id,
                        SQLOrganizationMember.user_id == user_id
                    ).first()
                
                if not current_member:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You are not a member of this organization"
                    )
                
                if current_member.role != 'owner':
                    # Check if user is trying to remove themselves
                    if member_id != current_member.id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only owners can remove members"
                        )
                
                # Get member to remove
                member = session.query(SQLOrganizationMember)\
                    .filter(
                        SQLOrganizationMember.id == member_id,
                        SQLOrganizationMember.organization_id == org_id
                    ).first()
                
                if not member:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Target member not found"
                    )
                
                # Check owner count if removing an owner
                if member.role == 'owner':
                    owners_count = session.query(SQLOrganizationMember)\
                        .filter(
                            SQLOrganizationMember.organization_id == org_id,
                            SQLOrganizationMember.role == 'owner'
                        ).count()
                    
                    if owners_count <= 1:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot remove the only owner"
                        )
                
                # Remove member
                session.delete(member)
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to remove member: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member"
            )
