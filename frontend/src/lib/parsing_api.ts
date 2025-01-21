import { config } from '@/config'
import { DocumentType } from '@/types/document'

export const parsingApi = {
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

    reindexDocument: async (
        documentId: string, 
        document: DocumentType,
        onProgress?: (status: string, progress: number) => void
    ) => {
        try {
            onProgress?.("Starting reindex process...", 0);
            
            console.log("Starting reindex with document:", {
                id: document.id,
                file_path: document.file_path,
                parser: document.parser,
                parserModified: document.parserModified
            });

            // Call the reindex endpoint directly with the parser
            const response = await fetch(`${config.apiUrl}/ingestion/reindex`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    document_id: documentId,
                    parser: document.parser
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error("Reindex error response:", errorData);
                throw new Error(`Failed to reindex document: ${JSON.stringify(errorData)}`);
            }

            const result = await response.json();
            onProgress?.("Reindex completed", 100);
            console.log("reindex response", result);
            return result;
            
        } catch (error) {
            onProgress?.("Error occurred", 0);
            console.error('Error reindexing document:', error);
            throw error;
        }
    }
}; 