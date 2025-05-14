import apiClient from './http/client';
import { AxiosError } from 'axios';

// Define the structure of the Config object based on KnowledgeConfigPage.tsx
// This can be expanded or imported from a shared types directory if it exists
interface LLMConfig {
  provider: string;
  model_name: string;
  api_key?: string;
  base_url?: string;
  temperature: number;
  streaming: boolean;
  max_tokens: number | null;
  additional_params: Record<string, unknown>;
}

interface EmbeddingConfig {
  provider: string;
  model_name: string;
  device: string;
  additional_params: Record<string, unknown>;
}

interface VectorStoreConfig {
  provider: string;
  collection_name: string;
  additional_params: Record<string, unknown>;
}

interface RetrievalParams {
  score_threshold: number;
  prioritize_semantic: boolean;
  weights: number[];
  reranker_model: string;
  reranker_threshold: number;
}

interface RetrievalConfig {
  method: string;
  k: number;
  params: RetrievalParams;
}

interface ProjectConfig {
  name: string;
  version: string;
  api_version: string;
}

interface DatabaseConfig {
  provider: string;
  additional_params: Record<string, unknown>;
}

interface StorageConfig {
  provider: string;
  minio_endpoint?: string;
  minio_access_key?: string;
  minio_secret_key?: string;
  minio_bucket?: string;
  minio_secure?: boolean;
}

interface CeleryConfig {
  broker_url: string;
  result_backend: string;
}

interface ChunkingConfig {
  chunk_size: number;
  chunk_overlap: number;
}

export interface KnowledgePageConfig { // Exporting this type for use in the page component
  llm?: LLMConfig;
  embedding?: EmbeddingConfig;
  vector_store?: VectorStoreConfig;
  retrieval?: RetrievalConfig;
  project?: ProjectConfig;
  database?: DatabaseConfig;
  storage?: StorageConfig;
  celery?: CeleryConfig;
  chunking?: ChunkingConfig;
}

interface BackendErrorDetail {
  detail?: string;
}

class KnowledgeConfigApi {
  async getConfig(): Promise<KnowledgePageConfig> {
    try {
      // The apiClient's request interceptor automatically adds the Authorization header.
      const response = await apiClient.get<KnowledgePageConfig>('/config');
      return response.data;
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>; 
      console.error('Failed to fetch knowledge configuration:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to fetch knowledge configuration (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }
}

// Export a single instance of the API service
export const knowledgeConfigApi = new KnowledgeConfigApi(); 