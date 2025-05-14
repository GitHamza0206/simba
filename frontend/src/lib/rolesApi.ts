import apiClient from './http/client';
import { AxiosError } from 'axios';

// Define and export Role and Permission interfaces
export interface Role {
  id: number;
  name: string;
  description: string;
}

export interface Permission {
  id: number;
  name: string;
  description: string;
}

// Common error structure (can be moved to a shared types file later if used widely)
interface BackendErrorDetail {
  detail?: string;
}

class RolesApi {
  async getRoles(): Promise<Role[]> {
    try {
      const response = await apiClient.get<Role[]>('/api/roles');
      return response.data;
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>; 
      console.error('Failed to fetch roles:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to fetch roles (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }

  async getPermissions(): Promise<Permission[]> {
    try {
      const response = await apiClient.get<Permission[]>('/api/roles/permissions');
      return response.data;
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>; 
      console.error('Failed to fetch permissions:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to fetch permissions (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }

  async getUserPermissions(userId: string): Promise<Permission[]> {
    try {
      const response = await apiClient.get<Permission[]>(`/api/roles/user/${userId}/permissions`);
      return response.data;
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>; 
      console.error('Failed to fetch user permissions:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to fetch user permissions for user ${userId} (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }
}

// Export a single instance of the API service
export const rolesApi = new RolesApi(); 