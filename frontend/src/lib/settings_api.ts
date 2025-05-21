import httpClient from '@/lib/http/client';
import { AxiosError } from 'axios';

export interface LLMConfig {
  provider: string;
  model_name: string;
  api_key?: string;
  base_url?: string;
  temperature?: number;
  streaming?: boolean;
  max_tokens?: number | null;
  additional_params?: Record<string, unknown>;
}

export interface EmbeddingConfig {
  provider: string;
  model_name: string;
  device: string;
  additional_params?: Record<string, unknown>;
}

export interface VectorStoreConfig {
  provider: string;
  additional_params?: Record<string, unknown>;
}

export interface RetrievalConfig {
  method: string;
  k: number;
  params?: Record<string, unknown>;
}

export interface ProjectConfig {
  name: string;
  version: string;
  api_version: string;
}

export interface DatabaseConfig {
  provider: string;
  additional_params?: Record<string, unknown>;
}

export interface StorageConfig {
  provider: string;
  minio_endpoint?: string | null;
  minio_access_key?: string | null;
  minio_secret_key?: string | null;
  minio_bucket?: string | null;
  minio_secure?: boolean;
  supabase_bucket?: string | null;
}

export interface CeleryConfig {
  broker_url: string;
  result_backend: string;
}

export interface AppConfig {
  llm: LLMConfig;
  embedding: EmbeddingConfig;
  vector_store: VectorStoreConfig;
  retrieval: RetrievalConfig;
  project: ProjectConfig;
  database: DatabaseConfig;
  storage: StorageConfig;
  celery: CeleryConfig;
}

/**
 * Fetches the application configuration from the backend.
 */
export const getAppSettings = async (): Promise<AppConfig> => {
  try {
    const response = await httpClient.get<AppConfig>('/config', {
      headers: {
        'Accept': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    const axiosError = error as AxiosError;
    let errorDetail = 'Failed to retrieve configuration due to network or server error.';

    if (axiosError.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      const errorData = axiosError.response.data as any;
      errorDetail = errorData?.detail || JSON.stringify(errorData) || axiosError.message;
      
      // Log HTML response if any for debugging (less common with Axios direct data access)
      if (typeof errorData === 'string' && errorData.trim().startsWith('<')) {
        console.error('Full HTML response from server:', errorData);
        errorDetail = `Server returned HTML response (status ${axiosError.response.status})`;
      }
    } else if (axiosError.request) {
      // The request was made but no response was received
      errorDetail = 'No response received from server while fetching app settings.';
      console.error('Error fetching app settings (no response):', axiosError.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      errorDetail = axiosError.message;
      console.error('Error fetching app settings (setup):', axiosError.message);
    }
    
    throw new Error(
      `Failed to fetch app settings. Status: ${axiosError.response?.status || 'N/A'}. Detail: ${errorDetail}`
    );
  }
}; 