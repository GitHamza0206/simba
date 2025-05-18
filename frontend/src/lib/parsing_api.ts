import { SimbaDoc } from '@/types/document';
import httpClient from './http/client';
import { AxiosError } from 'axios';

export const parsingApi = {
  /**
   * Get a list of supported parsers from the API
   */
  getParsers: async (): Promise<string[]> => {
    try {
      const response = await httpClient.get<{ parsers: string[] | string }>('/parsers');
      
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
    
    const response = await httpClient.post<{ task_id?: string } | SimbaDoc>('/parse', {
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
    const response = await httpClient.get(`/parsing/tasks/${taskId}`);
    return response.data;
  },

  /**
   * Start generating a summary for a document
   * Returns a task_id if the request was accepted, which can be used with getSummaryStatus.
   */
  generateSummary: async (documentId: string, prioritize: boolean = false): Promise<{ task_id?: string; message?: string; status?: string }> => {
    console.log(`Requesting summary generation for document ${documentId}, prioritize: ${prioritize}`);
    try {
      const response = await httpClient.post<{ task_id: string; message: string; status: string }>(
        '/summarize',
        { document_id: documentId, prioritize: prioritize } // Pass the prioritize flag
      );
      console.log("generateSummary response:", response.data);
      // Ensure task_id is part of the successful response structure for polling
      return { task_id: response.data.task_id, message: response.data.message, status: response.data.status };
    } catch (error) {
      console.error('Error generating summary:', error);
      if (error instanceof AxiosError && error.response && error.response.data && error.response.data.detail) {
        return { message: `Error: ${error.response.data.detail}`, status: 'error' };
      }
      return { message: 'Failed to start summary generation', status: 'error' };
    }
  },

  /**
   * Get the status of a summary generation task
   */
  getSummaryStatus: async (taskId: string): Promise<{
    task_id: string;
    status: string; // e.g., PENDING, STARTED, SUCCESS, FAILURE
    result?: {
      status: 'success' | 'error' | 'skipped';
      document_id?: string;
      error?: string;
      reason?: string; // For skipped status
    } | null; // Celery result is null if task is not ready
    message?: string;
  }> => {
    console.log(`Fetching status for summary task ${taskId}`);
    try {
      const response = await httpClient.get(`/summarize/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching status for summary task ${taskId}:`, error);
      let errorMessage = 'Failed to fetch summary task status';
      if (error instanceof AxiosError && error.response && error.response.data && error.response.data.detail) {
        errorMessage = `Error: ${error.response.data.detail}`;
      }
      // Return an error structure consistent with what the frontend might expect
      return { task_id: taskId, status: 'ERROR_FETCHING_STATUS', message: errorMessage, result: null };
    }
  }
}; 