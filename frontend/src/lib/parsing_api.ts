import { config } from '@/config'
import { DocumentType } from '@/types/document'

export const parsingApi = {
    getParsers: async (): Promise<{ parsers: string[] }> => {
        try {
            const response = await fetch(`${config.apiUrl}/parsers`);
            if (!response.ok) return { parsers: [] };
            return response.json();
        } catch (error) {
            console.error('Parser service unavailable:', error);
            return { parsers: [] };
        }
    },

    parseDocument: async (documentId: string, parser: string): Promise<SimbaDoc> => {
        const response = await fetch(`${config.apiUrl}/parse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ document_id: documentId, parser: parser })
        });
    }
}; 