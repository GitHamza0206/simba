"use client";

import { useState, useEffect, useMemo, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Bot, Trash2, Database, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useChat, useCollections } from "@/hooks";
import { API_URL } from "@/lib/constants";

// Chat components
import {
  ChatContainer,
  ChatEmptyState,
  ChatMessage,
  ChatInput,
  ChatStatus,
} from "@/components/chat";

function PlaygroundContent() {
  const [text, setText] = useState("");
  const searchParams = useSearchParams();
  const router = useRouter();

  // Get conversation ID from URL
  const conversationIdFromUrl = searchParams.get("conversation");

  // Handle conversation ID changes - update URL
  const handleConversationChange = useCallback(
    (newConversationId: string | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (newConversationId) {
        params.set("conversation", newConversationId);
      } else {
        params.delete("conversation");
      }
      router.replace(`?${params.toString()}`, { scroll: false });
    },
    [searchParams, router]
  );

  // Fetch available collections
  const { data: collectionsData, isLoading: collectionsLoading } = useCollections();
  const collections = useMemo(
    () => collectionsData?.items ?? [],
    [collectionsData?.items]
  );

  const {
    messages,
    status,
    collection,
    setCollection,
    isThinking: _isThinking,
    isLoadingHistory,
    sendMessage,
    stop,
    clear,
  } = useChat({
    initialConversationId: conversationIdFromUrl,
    onConversationChange: handleConversationChange,
    onError: (error) => {
      console.error("Chat error:", error);
    },
  });

  // Auto-select first collection when loaded
  useEffect(() => {
    if (!collection && collections.length > 0) {
      setCollection(collections[0].name);
    }
  }, [collection, collections, setCollection]);

  const handleSubmit = () => {
    if (!text.trim()) return;
    if (!collection) {
      console.error("No collection selected");
      return;
    }
    sendMessage(text);
    setText("");
  };

  const isStreaming = status === "streaming";
  const isSubmitted = status === "submitted";
  const isLoading = isStreaming || isSubmitted;

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      {/* Header */}
      <div className="flex items-center justify-between pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Playground</h1>
          <p className="text-muted-foreground">
            Test the chat experience with streaming responses.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Collection Selector */}
          <Select
            value={collection || ""}
            onValueChange={setCollection}
            disabled={isLoading || collectionsLoading}
          >
            <SelectTrigger className="w-[200px]">
              <Database className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Select collection" />
            </SelectTrigger>
            <SelectContent>
              {collections.length === 0 ? (
                <SelectItem value="_none" disabled>
                  No collections available
                </SelectItem>
              ) : (
                collections.map((col) => (
                  <SelectItem key={col.id} value={col.name}>
                    {col.name}
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            onClick={clear}
            disabled={messages.length === 0 || isLoading}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Clear Chat
          </Button>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex flex-1 flex-col overflow-hidden rounded-lg border bg-background">
        {isLoadingHistory ? (
          <div className="flex flex-1 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : messages.length === 0 ? (
          <ChatEmptyState
            title="Start a conversation"
            description={
              collection
                ? `Ask questions about documents in the "${collection}" collection.`
                : "Select a collection to start chatting."
            }
            icon={<Bot className="h-8 w-8" />}
          />
        ) : (
          <ChatContainer>
            {messages.map((message, idx) => (
              <ChatMessage
                key={message.id}
                message={message}
                isStreaming={isStreaming && idx === messages.length - 1}
              />
            ))}
            {/* Show status when waiting for first content */}
            {isStreaming &&
              messages.length > 0 &&
              !messages[messages.length - 1]?.content &&
              !messages[messages.length - 1]?.tools?.some(t => t.status === "running") && (
                <div className="flex gap-3 py-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <ChatStatus isThinking />
                  </div>
                </div>
              )}
          </ChatContainer>
        )}

        {/* Input */}
        <div className="border-t p-4">
          <ChatInput
            value={text}
            onChange={setText}
            onSubmit={handleSubmit}
            onStop={stop}
            status={status}
            placeholder={
              collection
                ? "Type your message..."
                : "Select a collection first..."
            }
            disabled={!collection}
          />
          <p className="mt-2 text-xs text-muted-foreground">
            Press Enter to send, Shift+Enter for new line. Connected to: {API_URL}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function PlaygroundPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <PlaygroundContent />
    </Suspense>
  );
}
