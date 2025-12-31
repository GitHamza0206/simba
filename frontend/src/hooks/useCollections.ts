import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";
import type { Collection, CollectionCreate, ListResponse } from "@/types/api";

const COLLECTIONS_KEY = ["collections"];

export function useCollections() {
  return useQuery({
    queryKey: COLLECTIONS_KEY,
    queryFn: () => api.get<ListResponse<Collection>>(API_ROUTES.COLLECTIONS),
  });
}

export function useCollection(collectionId: string) {
  return useQuery({
    queryKey: [...COLLECTIONS_KEY, collectionId],
    queryFn: () => api.get<Collection>(`${API_ROUTES.COLLECTIONS}/${collectionId}`),
    enabled: !!collectionId,
  });
}

export function useCreateCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CollectionCreate) =>
      api.post<Collection>(API_ROUTES.COLLECTIONS, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY });
    },
  });
}

export function useDeleteCollection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (collectionId: string) =>
      api.delete(`${API_ROUTES.COLLECTIONS}/${collectionId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COLLECTIONS_KEY });
    },
  });
}
