import { config } from '@/config';

/**
 * API service for document preview functionality
 */
class PreviewApi {
  private baseUrl = config.apiUrl;

  /**
   * Gets the URL for previewing a document
   * @param docId The ID of the document to preview
   * @returns The URL to use in an iframe for document preview
   */
  getPreviewUrl(docId: string): string {
    return `${this.baseUrl}/preview/${docId}`;
  }

  /**
   * Directly open a document in a new tab
   * @param docId The ID of the document to open
   */
  openDocumentInNewTab(docId: string): void {
    window.open(this.getPreviewUrl(docId), '_blank');
  }
}

// Export a single instance
export const previewApi = new PreviewApi(); 