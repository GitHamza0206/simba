import { config } from '@/config';
import { FolderType } from '@/types/document';

export const folderApi = {
  createFolder: async (name: string, parentPath: string = '/'): Promise<FolderType> => {
    try {
      const response = await fetch(`${config.apiUrl}/folders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, parent_path: parentPath }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to create folder');
      }

      return response.json();
    } catch (error) {
      console.error('Error creating folder:', error);
      throw error;
    }
  },

  moveDocument: async (documentId: string, targetFolderId: string): Promise<void> => {
    try {
      const response = await fetch(`${config.apiUrl}/folders/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentId,
          folder_id: targetFolderId,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to move document');
      }
    } catch (error) {
      console.error('Error moving document:', error);
      throw error;
    }
  },

  getFolders: async (): Promise<FolderType[]> => {
    try {
      const response = await fetch(`${config.apiUrl}/folders`, {
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch folders');
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching folders:', error);
      throw error;
    }
  },
}; 