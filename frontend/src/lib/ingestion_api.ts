import { SimbaDoc } from '@/types/document';
import httpClient from './http/client';

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
        throw new Error(`File type not supported for ${file.name}`);
      }
      if (file.size === 0 || file.size > MAX_FILE_SIZE) {
        throw new Error(`Invalid file size for ${file.name}`);
      }
    }

    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await httpClient.post<SimbaDoc[]>('/ingestion', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async uploadDocument(file: File): Promise<SimbaDoc[]> {
    return this.uploadDocuments([file]);
  }

  async getDocuments(): Promise<SimbaDoc[]> {
    const response = await httpClient.get<Record<string, SimbaDoc>>('/ingestion');
    const data = response.data;
    
    if (!data || Object.keys(data).length === 0) {
      return [];
    }
    
    return Object.values(data);
  }

  async getDocument(id: string): Promise<SimbaDoc> {
    const response = await httpClient.get<SimbaDoc>(`/ingestion/${id}`);
    return response.data;
  }

  async deleteDocument(id: string): Promise<void> {
    const isConfirmed = window.confirm('Are you sure you want to delete this document?');
    if (!isConfirmed) {
      throw new Error('Delete cancelled by user');
    }

    await httpClient.delete('/ingestion', {
      data: [id]
    });
  }

  async deleteDocumentWithoutConfirmation(id: string): Promise<void> {
    await httpClient.delete('/ingestion', {
      data: [id]
    });
  }

  async updateDocument(id: string, document: SimbaDoc): Promise<SimbaDoc> {
    const response = await httpClient.put<SimbaDoc>(`/ingestion/update_document?doc_id=${id}`, document);
    return response.data;
  }
}

// Export a single instance
export const ingestionApi = new IngestionApi();
