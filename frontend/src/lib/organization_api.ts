import httpClient from './http/client';

export interface Organization {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
}

export interface OrganizationMember {
  id: string;
  user_id: string;
  name: string;
  email: string;
  role: MemberRole;
  joined_at: string;
}

export type MemberRole = 'owner' | 'admin' | 'member' | 'viewer';

export interface OrganizationCreate {
  name: string;
}

export interface OrganizationMemberInvite {
  email: string;
  role: MemberRole;
}

export interface OrganizationMemberUpdate {
  role: MemberRole;
}

export const organizationApi = {
  // Get all organizations for the current user
  getOrganizations: async (): Promise<Organization[]> => {
    try {
      const response = await httpClient.get('/organizations');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
      throw error;
    }
  },

  // Create a new organization
  createOrganization: async (organization: OrganizationCreate): Promise<Organization> => {
    try {
      const response = await httpClient.post('/organizations', organization);
      return response.data;
    } catch (error) {
      console.error('Failed to create organization:', error);
      throw error;
    }
  },

  // Get organization by ID
  getOrganization: async (orgId: string): Promise<Organization> => {
    try {
      const response = await httpClient.get(`/organizations/${orgId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch organization:', error);
      throw error;
    }
  },

  // Get organization members
  getOrganizationMembers: async (orgId: string): Promise<OrganizationMember[]> => {
    try {
      const response = await httpClient.get(`/organizations/${orgId}/members`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch organization members:', error);
      throw error;
    }
  },

  // Invite a member to an organization
  inviteMember: async (orgId: string, invite: OrganizationMemberInvite): Promise<OrganizationMember> => {
    try {
      const response = await httpClient.post(`/organizations/${orgId}/invite`, invite);
      return response.data;
    } catch (error) {
      console.error('Failed to invite member:', error);
      throw error;
    }
  },

  // Update a member's role
  updateMemberRole: async (orgId: string, memberId: string, update: OrganizationMemberUpdate): Promise<OrganizationMember> => {
    try {
      const response = await httpClient.put(`/organizations/${orgId}/members/${memberId}`, update);
      return response.data;
    } catch (error) {
      console.error('Failed to update member role:', error);
      throw error;
    }
  },

  // Remove a member from an organization
  removeMember: async (orgId: string, memberId: string): Promise<void> => {
    try {
      await httpClient.delete(`/organizations/${orgId}/members/${memberId}`);
    } catch (error) {
      console.error('Failed to remove member:', error);
      throw error;
    }
  }
}; 