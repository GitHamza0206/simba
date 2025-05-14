import { SimbaDoc } from '@/types/document';
import apiClient from './http/client';

export const parsingApi = {
  /**
   * Get a list of supported parsers from the API
   */
  getParsers: async (): Promise<string[]> => {
    try {
      const response = await apiClient.get<{ parsers: string[] | string }>('/parsers');
      const data = response.data;
      
      if (typeof data.parsers === 'string') {
        return [data.parsers];
      }
      if (Array.isArray(data.parsers)) {
        return data.parsers;
      }
      console.warn('Unexpected parsers response format:', data);
      return ['docling']; // Default fallback
    } catch (error) {
      console.error('Error fetching parsers:', error);
      return ['docling']; // Default fallback on error
    }
  },

  /**
   * Start parsing a document
   */
  startParsing: async (documentId: string, parser: string): Promise<{ task_id?: string } | SimbaDoc> => {
    try {
      const sync = parser === 'mistral_ocr' ? true : false;
      console.log(`Starting parsing for ${documentId} using ${parser} (sync: ${sync})`);
      
      const response = await apiClient.post<{ task_id?: string } | SimbaDoc>('/parse', {
        document_id: documentId,
        parser: parser,
        sync: sync
      });
      
      console.log('Parse response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error starting parsing:', error);
      throw error;
    }
  },

  /**
   * Get the status of a parsing task
   */
  getParseStatus: async (taskId: string): Promise<{
    status: string;
    progress?: number;
    result?: {
      status: 'success' | 'error';
      document_id?: string;
      error?: string;
    };
  }> => {
    try {
      const response = await apiClient.get(`/parsing/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching parse status:', error);
      throw error;
    }
  }
}; 