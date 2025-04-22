/**
 * Central export point for all API services
 * This helps maintain clean code structure by isolating API calls
 * from UI components.
 */

// Import all API services
import { ingestionApi } from './ingestion_api';
import { embeddingApi } from './embedding_api';
import { previewApi } from './preview_api';
import { folderApi } from './folder_api';
import { parsingApi } from './parsing_api';
import { apiKeyService, ApiKey, ApiKeyResponse, ApiKeyCreate } from './api_key_service';

// Re-export all services and types
export {
  ingestionApi,
  embeddingApi,
  previewApi,
  folderApi,
  parsingApi,
  apiKeyService,
};

export type {
  ApiKey,
  ApiKeyResponse,
  ApiKeyCreate,
};

// Example usage in components:
// import { ingestionApi, previewApi, apiKeyService, type ApiKey } from '@/lib/api_services'; 