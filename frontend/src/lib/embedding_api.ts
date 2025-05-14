import apiClient from './http/client'; // Import the new Axios client
import { AxiosError } from 'axios'; // Import AxiosError for type safety
// config import might not be needed if apiClient has baseURL set

// Define expected response types for clarity and to fix linter errors
interface EmbedDocumentResponse {
  // Define the structure of the successful response from POST /embed/document
  // Example: taskId: string; message: string; status: string;
  [key: string]: unknown; // Using unknown instead of any
}

interface DeleteDocumentResponse {
  // Define the structure of the successful response from DELETE /embed/document
  // Example: message: string; docId: string;
  [key: string]: unknown; // Using unknown instead of any
}

interface BackendErrorDetail {
  detail?: string;
}

// Helper function to add delay (can be kept or moved to a utils file)
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const embeddingApi = {
    
    embedd_document: async (docId: string, retries = 1): Promise<EmbedDocumentResponse> => {
        try {
            console.log(`Attempting to embed document ${docId}, attempt ${retries}`);
            // The apiClient will automatically add Authorization header via interceptor
            // Axios also automatically sets Content-Type: application/json for object bodies (if any)
            // If this POST request doesn't have a body, the second argument to post can be null or an empty object.
            const response = await apiClient.post<EmbedDocumentResponse>(`/embed/document?doc_id=${docId}`, null); // Assuming no body for this POST
            return response.data;
        } catch (e: unknown) { // Use unknown for initial catch, then type guard
            const error = e as AxiosError<BackendErrorDetail>; // More specific error data type
            if (error.response && error.response.status === 500 && retries < 2) {
                console.log(`Server error when embedding document. Will retry after delay...`);
                await delay(1000); // Wait 1 second before retrying
                return embeddingApi.embedd_document(docId, retries + 1); // Recursive call
            }
            console.error('Error embedding document:', error.response?.data || error.message || error);
            // Extract detail from error.response.data if it exists and has a detail property
            const detail = error.response?.data?.detail;
            throw new Error(detail || `Failed to embed document (HTTP ${error.response?.status || 'Unknown'})`);
        }
    },
    
    delete_document: async (docId: string): Promise<DeleteDocumentResponse> => {
        try {
            console.log('Deleting document embeddings with ID:', docId);
            // apiClient will add Authorization header
            const response = await apiClient.delete<DeleteDocumentResponse>(`/embed/document?doc_id=${docId}`);
            return response.data;
        } catch (e: unknown) { // Use unknown for initial catch, then type guard
            const error = e as AxiosError<BackendErrorDetail>; // More specific error data type
            console.error('Delete document error:', error.response?.data || error.message || error);
            // Extract detail from error.response.data if it exists and has a detail property
            const detail = error.response?.data?.detail;
            throw new Error(detail || `Failed to delete document embeddings (HTTP ${error.response?.status || 'Unknown'})`);
        }
    }
}

