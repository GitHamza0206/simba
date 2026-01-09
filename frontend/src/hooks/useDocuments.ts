import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { API_URL } from "@/lib/constants";
import { useAuth } from "@/providers/auth-provider";
import type { Document, DocumentUploadResponse, ListResponse } from "@/types/api";

const DOCUMENTS_KEY = ["documents"];

// Get org ID from localStorage for mutations
function getOrgHeader(): Record<string, string> {
  const orgId = typeof window !== "undefined" ? localStorage.getItem("simba_active_org") : null;
  return orgId ? { "X-Organization-Id": orgId } : {};
}

interface UseDocumentsOptions {
  collectionId?: string;
  status?: string;
}

export function useDocuments(options: UseDocumentsOptions = {}) {
  const { collectionId, status } = options;
  const { isReady } = useAuth();

  return useQuery({
    queryKey: [...DOCUMENTS_KEY, { collectionId, status }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (collectionId) params.set("collection_id", collectionId);
      if (status) params.set("status", status);

      const queryString = params.toString();
      const endpoint = `/api/v1/documents${queryString ? `?${queryString}` : ""}`;

      return api.get<ListResponse<Document>>(endpoint);
    },
    enabled: isReady,
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
  const { isReady } = useAuth();

  return useQuery({
    queryKey: [...DOCUMENTS_KEY, documentId],
    queryFn: () => api.get<Document>(`/api/v1/documents/${documentId}`),
    enabled: isReady && !!documentId,
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
          headers: getOrgHeader(),
          credentials: "include",
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
      return api.delete(`/api/v1/documents/${documentId}`);
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
      return api.post(`/api/v1/documents/${documentId}/reprocess`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY });
    },
  });
}

export function useDocumentDownloadUrl(documentId: string) {
  const { isReady } = useAuth();

  return useQuery({
    queryKey: [...DOCUMENTS_KEY, documentId, "download"],
    queryFn: () => api.get<{ download_url: string; filename: string }>(`/api/v1/documents/${documentId}/download`),
    enabled: isReady && !!documentId,
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
  const { isReady } = useAuth();

  return useQuery({
    queryKey: [...DOCUMENTS_KEY, documentId, "chunks"],
    queryFn: () => api.get<ChunksResponse>(`/api/v1/documents/${documentId}/chunks`),
    enabled: isReady && !!documentId,
  });
}
