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
// Re-export all services
export {
  ingestionApi,
  embeddingApi,
  previewApi,
  folderApi,
  parsingApi,

};

// Example usage in components:
// import { ingestionApi, previewApi } from '@/lib/api_services'; 