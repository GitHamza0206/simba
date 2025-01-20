import { config } from '@/config';
import { DocumentType } from '@/types/document';

const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB
const ALLOWED_FILE_TYPES = [
  'application/pdf',
  'text/plain',
  'text/markdown',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];

interface ValidationResult {
  isValid: boolean;
  error?: string;
}

interface IngestionResponse {
  message: string;
}

interface GetDocumentsResponse {
  message: string;
  documents: Record<string, DocumentType>;
}

export const ingestionApi = {
  validateFile: (file: File): ValidationResult => {
    if (!file) return { isValid: false, error: "No file selected" };
    
    if (!ALLOWED_FILE_TYPES.includes(file.type)) {
      return { isValid: false, error: "File type not supported" };
    }

    if (file.size === 0) {
      return { isValid: false, error: "File is empty" };
    }

    if (file.size > MAX_FILE_SIZE) {
      return { isValid: false, error: "File size exceeds 200MB limit" };
    }

    return { isValid: true };
  },

  uploadDocument: async (file: File, onProgress?: (progress: number) => void): Promise<IngestionResponse> => {
    const validation = ingestionApi.validateFile(file);
    if (!validation.isValid) {
      throw new Error(validation.error);
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const response = await fetch(`${config.apiUrl}/ingestion`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Upload failed');
      }

      return response.json();
    } catch (error:any) {
      if (error.name === 'AbortError') {
        throw new Error('Upload timeout - please try again');
      }
      throw error;
    }
  },

  getLoaders: async (): Promise<string[]> => {
    const response = await fetch(`${config.apiUrl}/loaders`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    if (!response.ok) {
      throw new Error('Failed to fetch loaders');
    }
    return response.json(); 
  },  

  getParsers: async (): Promise<{ parsers: string[] }> => {
    const response = await fetch(`${config.apiUrl}/parsers`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    if (!response.ok) {
      throw new Error('Failed to fetch parsers');
    }
    return response.json();
  },

  getDocuments: async (): Promise<DocumentType[]> => {
    const response = await fetch(`${config.apiUrl}/ingestion`, {
      cache: 'no-cache',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch documents');
    }
    
    const data = await response.json();
    if (!data || Object.keys(data).length === 0) return [];

    console.log(data);
    
    return Object.entries(data).map(([id, doc]: [string, any]) => ({
      id,
      document_id: doc.id,
      name: doc.metadata.filename || 'Unknown',
      type: doc.metadata.type || 'Unknown',
      size: (doc.metadata.size || 0) + " MB",
      uploadedAt: doc.metadata.uploadedAt || 'Unknown',
      content: doc.page_content || 'Unknown',
      loader: doc.metadata.loader || 'Unknown',
      parser: doc.metadata.parser || '-',
      file_path: doc.metadata.file_path || 'none',

    }));
  },

  deleteDocument: async (uid: string): Promise<IngestionResponse> => {
    // Demander confirmation à l'utilisateur
    const isConfirmed = window.confirm('Are you sure you want to delete this document?');
    
    if (!isConfirmed) {
      throw new Error('Delete cancelled by user');
    }

    try {
      const response = await fetch(`${config.apiUrl}/ingestion?uid=${uid}`, {
        method: 'DELETE',
        headers: {
          'accept': 'application/json'
        }
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Delete failed');
      }

      return response.json();
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete document');
    }
  },

  async getDocument(id: string): Promise<{ content: string; type: string }> {

    try {
      const response = await fetch(`${config.apiUrl}/document/${id}`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch document');
      }

      const data = await response.json();
      
      // Handle both PDF and text content
      return {
        content: data.content,
        type: data.type || 'text'
      };
    } catch (error) {
      console.error('Error fetching document:', error);
      throw error;
    }
  },

  
};
