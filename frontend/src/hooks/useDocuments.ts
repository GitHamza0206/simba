import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { API_URL } from "@/lib/constants";
import type { Document, DocumentUploadResponse, ListResponse } from "@/types/api";

const DOCUMENTS_KEY = ["documents"];

interface UseDocumentsOptions {
  collectionId?: string;
  status?: string;
}

export function useDocuments(options: UseDocumentsOptions = {}) {
  const { collectionId, status } = options;

  return useQuery({
    queryKey: [...DOCUMENTS_KEY, { collectionId, status }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (collectionId) params.set("collection_id", collectionId);
      if (status) params.set("status", status);

      const queryString = params.toString();
      const url = `${API_URL}/api/v1/documents${queryString ? `?${queryString}` : ""}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error("Failed to fetch documents");
      return response.json() as Promise<ListResponse<Document>>;
    },
    // Auto-refresh every 3s when documents are processing
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasProcessing = data?.items?.some(
        (doc) => doc.status === "pending" || doc.status === "processing"
      );
      return hasProcessing ? 3000 : false;
    },
  });
}

export function useDocument(documentId: string) {
  return useQuery({
    queryKey: [...DOCUMENTS_KEY, documentId],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/v1/documents/${documentId}`);
      if (!response.ok) throw new Error("Failed to fetch document");
      return response.json() as Promise<Document>;
    },
    enabled: !!documentId,
  });
}

interface UploadDocumentParams {
  file: File;
  collectionId: string;
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ file, collectionId }: UploadDocumentParams) => {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/api/v1/documents?collection_id=${collectionId}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to upload document");
      }

      return response.json() as Promise<DocumentUploadResponse>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => {
      const response = await fetch(`${API_URL}/api/v1/documents/${documentId}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to delete document");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}

export function useReprocessDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => {
      const response = await fetch(
        `${API_URL}/api/v1/documents/${documentId}/reprocess`,
        { method: "POST" }
      );
      if (!response.ok) throw new Error("Failed to reprocess document");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}

export function useDocumentDownloadUrl(documentId: string) {
  return useQuery({
    queryKey: [...DOCUMENTS_KEY, documentId, "download"],
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/api/v1/documents/${documentId}/download`
      );
      if (!response.ok) throw new Error("Failed to get download URL");
      return response.json() as Promise<{ download_url: string; filename: string }>;
    },
    enabled: !!documentId,
  });
}

export interface Chunk {
  id: string;
  text: string;
  position: number;
  document_name: string;
}

export interface ChunksResponse {
  document_id: string;
  document_name: string;
  chunk_count: number;
  chunks: Chunk[];
}

export function useDocumentChunks(documentId: string | null) {
  return useQuery({
    queryKey: [...DOCUMENTS_KEY, documentId, "chunks"],
    queryFn: async () => {
      const response = await fetch(
        `${API_URL}/api/v1/documents/${documentId}/chunks`
      );
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || "Failed to get chunks");
      }
      return response.json() as Promise<ChunksResponse>;
    },
    enabled: !!documentId,
  });
}
