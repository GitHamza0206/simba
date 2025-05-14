import apiClient from './http/client'; // Import the new Axios client
import { config } from '@/config';         // Keep for type interfaces if not for apiUrl directly

export interface Organization {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
}

export interface OrganizationMember {
  id: string;
  user_id: string;
  name?: string;
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
  getOrganizations: async (): Promise<Organization[]> => {
    try {
      const response = await apiClient.get('/organizations');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
      throw error; // Axios errors can be re-thrown
    }
  },

  createOrganization: async (organizationData: OrganizationCreate): Promise<Organization> => {
    try {
      const response = await apiClient.post('/organizations', organizationData);
      return response.data;
    } catch (error) {
      console.error('Failed to create organization:', error);
      throw error;
    }
  },

  getOrganization: async (orgId: string): Promise<Organization> => {
    try {
      const response = await apiClient.get(`/organizations/${orgId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch organization:', error);
      throw error;
    }
  },

  getOrganizationMembers: async (orgId: string): Promise<OrganizationMember[]> => {
    try {
      const response = await apiClient.get(`/organizations/${orgId}/members`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch organization members:', error);
      throw error;
    }
  },

  inviteMember: async (orgId: string, inviteData: OrganizationMemberInvite): Promise<OrganizationMember> => {
    try {
      const response = await apiClient.post(`/organizations/${orgId}/invite`, inviteData);
      return response.data;
    } catch (error) {
      console.error('Failed to invite member:', error);
      throw error;
    }
  },

  updateMemberRole: async (orgId: string, memberUserId: string, updateData: OrganizationMemberUpdate): Promise<OrganizationMember> => {
    try {
      const response = await apiClient.put(`/organizations/${orgId}/members/${memberUserId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Failed to update member role:', error);
      throw error;
    }
  },

  removeMember: async (orgId: string, memberUserId: string): Promise<void> => {
    try {
      // Axios DELETE typically doesn't return data, so we don't assign response.data
      await apiClient.delete(`/organizations/${orgId}/members/${memberUserId}`);
    } catch (error) {
      console.error('Failed to remove member:', error);
      throw error;
    }
  }
}; 