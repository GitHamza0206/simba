import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ConversationListItem, ListResponse, Message } from "@/types/api";

const CONVERSATIONS_KEY = ["conversations"];

export function useConversations() {
  return useQuery({
    queryKey: CONVERSATIONS_KEY,
    queryFn: () =>
      api.get<ListResponse<ConversationListItem>>("/api/v1/conversations"),
  });
}

export function useConversation(conversationId: string) {
  return useQuery({
    queryKey: [...CONVERSATIONS_KEY, conversationId],
    queryFn: () =>
      api.get<ConversationListItem>(`/api/v1/conversations/${conversationId}`),
    enabled: !!conversationId,
  });
}

export function useConversationMessages(conversationId: string) {
  return useQuery({
    queryKey: [...CONVERSATIONS_KEY, conversationId, "messages"],
    queryFn: () =>
      api.get<Message[]>(`/api/v1/conversations/${conversationId}/messages`),
    enabled: !!conversationId,
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conversationId: string) =>
      api.delete(`/api/v1/conversations/${conversationId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY });
    },
  });
}
