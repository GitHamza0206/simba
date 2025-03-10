import { config } from '@/config';

// Helper function to add delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const embeddingApi = {
    
    embedd_document: async (docId: string, retries = 1) => {
        try {
            console.log(`Attempting to embed document ${docId}, attempt ${retries}`);
            const response = await fetch(`${config.apiUrl}/embed/document?doc_id=${docId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                // For server errors (500), we might want to retry
                if (response.status === 500 && retries < 2) {
                    console.log(`Server error when embedding document. Will retry after delay...`);
                    await delay(1000); // Wait 1 second before retrying
                    return embeddingApi.embedd_document(docId, retries + 1);
                }
                
                const error = await response.json();
                throw new Error(error.detail || `Failed to embed document (HTTP ${response.status})`);
            }
            return response.json();
        } catch (error) {
            console.error('Error embedding document:', error);
            throw error;
        }
    },
    
    delete_document: async (docId: string) => {
        try {
            console.log('Deleting document with ID:', docId);
            
            const response = await fetch(`${config.apiUrl}/embed/document?doc_id=${docId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                const errorMessage = data.detail || JSON.stringify(data);
                throw new Error(errorMessage);
            }
            
            return data;
        } catch (error) {
            console.error('Delete document error:', error);
            if (error instanceof Error) {
                throw new Error(error.message);
            }
            throw new Error('Failed to delete document embeddings');
        }
    }
}

