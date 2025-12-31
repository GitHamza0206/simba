"use client";

import { useState } from "react";
import { MessageSquare, Search, Trash2, Loader2, Calendar } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useConversations, useDeleteConversation } from "@/hooks";
import type { ConversationListItem } from "@/types/api";

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // Less than 24 hours - show relative time
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000));
    if (hours < 1) {
      const minutes = Math.floor(diff / (60 * 1000));
      return minutes < 1 ? "Just now" : `${minutes}m ago`;
    }
    return `${hours}h ago`;
  }

  // Less than 7 days - show day name
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    return date.toLocaleDateString("en-US", { weekday: "long" });
  }

  // Otherwise show date
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}

function ConversationRow({
  conversation,
  onDelete,
  isDeleting,
}: {
  conversation: ConversationListItem;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  return (
    <div className="flex items-center justify-between border-b p-4 last:border-0 hover:bg-muted/50">
      <div className="flex items-center gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
          <MessageSquare className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="font-medium">Conversation {conversation.id.slice(0, 8)}...</p>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span>{conversation.message_count} messages</span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(conversation.created_at)}
            </span>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onDelete}
          disabled={isDeleting}
          className="text-red-600 hover:text-red-700"
        >
          {isDeleting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}

export default function ConversationsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading } = useConversations();
  const deleteMutation = useDeleteConversation();

  const conversations = data?.items ?? [];

  // Filter conversations by search query (by ID for now)
  const filteredConversations = searchQuery
    ? conversations.filter((c) =>
        c.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : conversations;

  const handleDelete = async (conversation: ConversationListItem) => {
    if (!confirm("Delete this conversation? This cannot be undone.")) return;

    setDeletingId(conversation.id);
    try {
      await deleteMutation.mutateAsync(conversation.id);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Conversations</h1>
        <p className="text-muted-foreground">
          View and manage customer conversations.
        </p>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="search"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-10 w-full rounded-md border bg-background pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      {/* Conversations List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Conversations</CardTitle>
          <CardDescription>
            {isLoading
              ? "Loading..."
              : `${filteredConversations.length} conversation(s)`}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <MessageSquare className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mt-4 text-lg font-semibold">
                {searchQuery ? "No matching conversations" : "No conversations yet"}
              </h3>
              <p className="mt-2 text-center text-sm text-muted-foreground">
                {searchQuery
                  ? "Try a different search term"
                  : "When customers start chatting with your widget, their conversations will appear here."}
              </p>
            </div>
          ) : (
            <div>
              {filteredConversations.map((conversation) => (
                <ConversationRow
                  key={conversation.id}
                  conversation={conversation}
                  onDelete={() => handleDelete(conversation)}
                  isDeleting={deletingId === conversation.id}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
