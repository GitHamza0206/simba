import httpClient from './http/client';

export interface ApiKey {
  id: string;
  key_prefix: string;
  tenant_id?: string;
  name: string;
  roles: string[];
  created_at: string;
  last_used?: string;
  is_active: boolean;
  expires_at?: string;
}

export interface ApiKeyResponse {
  id: string;
  key: string;
  key_prefix: string;
  tenant_id?: string;
  name: string;
  roles: string[];
  created_at: string;
  expires_at?: string;
}

export interface ApiKeyCreate {
  name: string;
  tenant_id?: string;
  roles?: string[];
  expires_at?: string;
}

export const apiKeyService = {
  // Get all API keys for the current user
  getApiKeys: async (tenantId?: string): Promise<ApiKey[]> => {
    try {
      const params = tenantId ? { tenant_id: tenantId } : undefined;
      const response = await httpClient.get('/api/api-keys', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
      throw error;
    }
  },

  // Create a new API key
  createApiKey: async (keyData: ApiKeyCreate): Promise<ApiKeyResponse> => {
    try {
      const response = await httpClient.post('/api/api-keys', keyData);
      return response.data;
    } catch (error) {
      console.error('Failed to create API key:', error);
      throw error;
    }
  },

  // Delete an API key
  deleteApiKey: async (keyId: string, tenantId?: string): Promise<void> => {
    try {
      const params = tenantId ? { tenant_id: tenantId } : undefined;
      await httpClient.delete(`/api/api-keys/${keyId}`, { params });
    } catch (error) {
      console.error('Failed to delete API key:', error);
      throw error;
    }
  },

  // Deactivate an API key
  deactivateApiKey: async (keyId: string, tenantId?: string): Promise<void> => {
    try {
      const params = tenantId ? { tenant_id: tenantId } : undefined;
      await httpClient.post(`/api/api-keys/${keyId}/deactivate`, null, { params });
    } catch (error) {
      console.error('Failed to deactivate API key:', error);
      throw error;
    }
  }
}; 