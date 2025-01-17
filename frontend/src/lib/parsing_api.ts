import { config } from '@/config'
import { DocumentType } from '@/types/document'

export const reindexDocument = async (
  documentId: string, 
  document: DocumentType,
  onProgress?: (status: string, progress: number) => void
) => {
  try {
    // Start progress
    onProgress?.("Starting reindex process...", 0);
    
    console.log("Starting reindex with document:", {
      id: document.id,
      file_path: document.file_path,
      parser: document.parser,
      parserModified: document.parserModified
    });
    
    if (document.parserModified) {
      onProgress?.("Parsing document...", 25);
      
      const requestData = {
        document_id: document.id,
        parser: document.parser
      };
      console.log("Sending parse request with:", requestData);

      const parseResponse = await fetch(`${config.apiUrl}/parse`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!parseResponse.ok) {
        const errorData = await parseResponse.json();
        console.error("Parse error response:", errorData);
        throw new Error(`Failed to parse document: ${JSON.stringify(errorData)}`);
      }

      const parseResult = await parseResponse.json();
      console.log("Parse result:", parseResult);
      onProgress?.("Parsing completed", 50);
    }

    // Now proceed with regular reindexing
    onProgress?.("Reindexing document...", 75);
    
    const response = await fetch(`${config.apiUrl}/ingestion/${documentId}/reindex`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        loader: document.loader,
        parser: document.parser,
        file_path: document.file_path
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Failed to reindex document: ${JSON.stringify(errorData)}`);
    }

    onProgress?.("Reindex completed", 100);
    return await response.json();
    
  } catch (error) {
    onProgress?.("Error occurred", 0);
    console.error('Error reindexing document:', error);
    throw error;
  }
}; 