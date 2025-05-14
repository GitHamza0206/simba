import { SimbaDoc } from '@/types/document';
import apiClient from './http/client'; // Import the new Axios client
import { AxiosError } from 'axios'; // Import AxiosError
// Config import might not be needed if apiClient has baseURL set

// Define a common error structure if your backend sends one, e.g., { detail: string }
interface BackendErrorDetail {
  detail?: string;
}

const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB
const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'text/plain',
  'text/markdown',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',  // .xls
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  // .xlsx
  'application/vnd.ms-powerpoint',  // .ppt
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'  // .pptx
];

class IngestionApi {

  async uploadDocuments(files: File[]): Promise<SimbaDoc[]> {
    // Validate all files
    for (const file of files) {
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        throw new Error(`File type not supported for ${file.name}: ${file.type}`);
      }
      if (file.size === 0 || file.size > MAX_FILE_SIZE) {
        throw new Error(`Invalid file size for ${file.name}: ${file.size} bytes`);
      }
    }

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      // Axios automatically sets Content-Type for FormData.
      // Auth header is added by the interceptor.
      const response = await apiClient.post<SimbaDoc[]>('/ingestion', formData);
      return response.data;
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>; 
      console.error('Failed to upload documents:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to upload documents (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }

  async uploadDocument(file: File): Promise<SimbaDoc[]> {
    return this.uploadDocuments([file]);
  }

  async getDocuments(): Promise<SimbaDoc[]> {
    try {
      const response = await apiClient.get<Record<string, SimbaDoc> | SimbaDoc[]>('/ingestion');
      // Backend might return a map {id: doc} or an array [doc]
      // This logic assumes it could be either, preferring array, then converting map.
      if (Array.isArray(response.data)) {
        return response.data;
      }
      if (response.data && typeof response.data === 'object' && !Array.isArray(response.data)) {
        const docMap = response.data as Record<string, SimbaDoc>;
        return Object.keys(docMap).length > 0 ? Object.values(docMap) : [];
      }
      return []; // Default to empty array if response is unexpected
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>; 
      console.error('Failed to get documents:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to get documents (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }

  async getDocument(id: string): Promise<SimbaDoc> {
    try {
      const response = await apiClient.get<SimbaDoc>(`/ingestion/${id}`);
      return response.data;
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>; 
      console.error('Failed to get document:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to get document ${id} (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }

  async deleteDocument(id: string): Promise<void> {
    const isConfirmed = window.confirm('Are you sure you want to delete this document?');
    if (!isConfirmed) {
      console.log('Document deletion cancelled by user.');
      return;
    }
    await this.deleteDocumentWithoutConfirmation(id);
  }

  async deleteDocumentWithoutConfirmation(id: string): Promise<void> {
    try {
      await apiClient.delete('/ingestion', { data: [id] }); // Send ID in data for DELETE body
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>; 
      console.error('Failed to delete document:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to delete document ${id} (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }

  async updateDocument(id: string, documentData: Partial<SimbaDoc>): Promise<SimbaDoc> {
    try {
      const response = await apiClient.put<SimbaDoc>(`/ingestion/update_document?doc_id=${id}`, documentData);
      return response.data;
    } catch (e: unknown) {
      const error = e as AxiosError<BackendErrorDetail>;
      console.error('Failed to update document:', error.response?.data || error.message || error);
      const detail = error.response?.data?.detail;
      throw new Error(detail || `Failed to update document ${id} (HTTP ${error.response?.status || 'Unknown'})`);
    }
  }
}

// Export a single instance
export const ingestionApi = new IngestionApi();
