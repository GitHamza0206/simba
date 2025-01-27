import { config } from '@/config';

export const embeddingApi = {
    
    embedd_document: async (docId: string) => {
        try {
            const response = await fetch(`${config.apiUrl}/embed/document?doc_id=${docId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to embed document');
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

