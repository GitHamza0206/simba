import { SimbaDoc } from '@/types/document';
import { authAxios } from './supabase';

export const parsingApi = {
  /**
   * Get a list of supported parsers from the API
   */
  getParsers: async (): Promise<string[]> => {
    try {
      const response = await authAxios.get<{ parsers: string[] | string }>('/parsers');
      
      // Handle string response (backward compatibility)
      if (typeof response.data.parsers === 'string') {
        return [response.data.parsers];
      }
      
      // Handle array response
      if (Array.isArray(response.data.parsers)) {
        return response.data.parsers;
      }
      
      console.warn('Unexpected parsers response format:', response.data);
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
    // For Mistral OCR, always use synchronous processing
    const sync = parser === 'mistral_ocr' ? true : false;
    
    console.log(`Starting parsing for ${documentId} using ${parser} (sync: ${sync})`);
    
    const response = await authAxios.post<{ task_id?: string } | SimbaDoc>('/parse', {
      document_id: documentId,
      parser: parser,
      sync: sync
    });
    
    // The response could be either a task_id (for docling) or a SimbaDoc (for Mistral OCR)
    console.log('Parse response:', response.data);
    return response.data;
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
    const response = await authAxios.get(`/parsing/tasks/${taskId}`);
    return response.data;
  }
}; 