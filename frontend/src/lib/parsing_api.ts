import { config } from '@/config';
import { SimbaDoc } from '@/types/document';

// Helper function for making API requests
const request = async <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
  const response = await fetch(`${config.apiUrl}${endpoint}`, {
    ...options,
    headers: {
      'Accept': 'application/json',
      ...options.headers,
    }
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || 'Request failed');
  }

  return response.json();
};

export const parsingApi = {
  /**
   * Get a list of supported parsers from the API
   */
  getParsers: async (): Promise<string[]> => {
    try {
      const response = await request<{ parsers: string[] | string }>('/parsers');
      
      // Handle string response (backward compatibility)
      if (typeof response.parsers === 'string') {
        return [response.parsers];
      }
      
      // Handle array response
      if (Array.isArray(response.parsers)) {
        return response.parsers;
      }
      
      console.warn('Unexpected parsers response format:', response);
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
    const sync = parser === 'mistral_ocr' || parser === 'isolated_docling' ? true : false;
    
    console.log(`Starting parsing for ${documentId} using ${parser} (sync: ${sync})`);
    
    const response = await request<{ task_id?: string } | SimbaDoc>('/parse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        document_id: documentId,
        parser: parser,
        sync: sync
      })
    });
    
    // The response could be either a task_id (for docling) or a SimbaDoc (for Mistral OCR)
    console.log('Parse response:', response);
    return response;
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
    return request(`/parsing/tasks/${taskId}`);
  }
}; 