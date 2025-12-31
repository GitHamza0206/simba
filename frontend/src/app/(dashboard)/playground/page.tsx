"use client";

import { useState, useEffect, useMemo } from "react";
import { Bot, Trash2, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useChat, useCollections, type ChatMessage } from "@/hooks";
import { API_URL } from "@/lib/constants";
import type { PromptInputMessage } from "@/components/ai-elements/prompt-input";

// ai-elements components
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
  ConversationEmptyState,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import {
  Reasoning,
  ReasoningTrigger,
  ReasoningContent,
} from "@/components/ai-elements/reasoning";
import {
  Sources,
  SourcesTrigger,
  SourcesContent,
  Source,
} from "@/components/ai-elements/sources";
import {
  Tool,
  ToolHeader,
  ToolContent,
  ToolInput,
  ToolOutput,
} from "@/components/ai-elements/tool";

function ChatMessageItem({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <Message from={message.role}>
      <div>
        {/* Sources - only for assistant messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <Sources>
            <SourcesTrigger count={message.sources.length} />
            <SourcesContent>
              {message.sources.map((source, idx) => (
                <Source key={idx} title={source.document_name}>
                  <span className="truncate max-w-[200px]">
                    {source.document_name}
                  </span>
                </Source>
              ))}
            </SourcesContent>
          </Sources>
        )}

        {/* Reasoning/Thinking - only for assistant messages */}
        {!isUser && message.thinking && (
          <Reasoning>
            <ReasoningTrigger />
            <ReasoningContent>{message.thinking}</ReasoningContent>
          </Reasoning>
        )}

        {/* Tool calls - only for assistant messages */}
        {!isUser &&
          message.tools &&
          message.tools.map((tool, idx) => (
            <Tool key={idx} defaultOpen={false}>
              <ToolHeader
                title={tool.name}
                type="tool-invocation"
                state={
                  tool.status === "running"
                    ? "input-available"
                    : tool.status === "error"
                      ? "output-error"
                      : "output-available"
                }
              />
              <ToolContent>
                {tool.input && <ToolInput input={tool.input} />}
                {(tool.output || tool.status === "error") && (
                  <ToolOutput
                    output={tool.output}
                    errorText={
                      tool.status === "error" ? "Tool execution failed" : undefined
                    }
                  />
                )}
              </ToolContent>
            </Tool>
          ))}

        {/* Message content */}
        <MessageContent>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <MessageResponse>{message.content}</MessageResponse>
          )}
        </MessageContent>
      </div>
    </Message>
  );
}

function ThinkingIndicator() {
  return (
    <Message from="assistant">
      <div>
        <Reasoning isStreaming>
          <ReasoningTrigger />
          <ReasoningContent>{""}</ReasoningContent>
        </Reasoning>
      </div>
    </Message>
  );
}

export default function PlaygroundPage() {
  const [text, setText] = useState("");

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
    isThinking,
    sendMessage,
    clear,
  } = useChat({
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

  const handleSubmit = (message: PromptInputMessage) => {
    if (!message.text?.trim()) return;
    if (!collection) {
      console.error("No collection selected");
      return;
    }
    sendMessage(message.text);
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
        {messages.length === 0 ? (
          <ConversationEmptyState
            title="Start a conversation"
            description={
              collection
                ? `Ask questions about documents in the "${collection}" collection.`
                : "Select a collection to start chatting."
            }
            icon={<Bot className="h-8 w-8" />}
          />
        ) : (
          <Conversation className="flex-1">
            <ConversationContent>
              {messages.map((message) => (
                <ChatMessageItem key={message.id} message={message} />
              ))}
              {isThinking &&
                !messages[messages.length - 1]?.thinking &&
                status === "streaming" && <ThinkingIndicator />}
            </ConversationContent>
            <ConversationScrollButton />
          </Conversation>
        )}

        {/* Input */}
        <div className="border-t p-4">
          <PromptInput onSubmit={handleSubmit}>
            <PromptInputBody>
              <PromptInputTextarea
                placeholder={
                  collection
                    ? "Type your message..."
                    : "Select a collection first..."
                }
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={isLoading || !collection}
              />
            </PromptInputBody>
            <PromptInputFooter>
              <PromptInputTools>
                {collection && (
                  <span className="text-xs text-muted-foreground">
                    Collection: {collection}
                  </span>
                )}
              </PromptInputTools>
              <PromptInputSubmit
                disabled={!text.trim() || isLoading || !collection}
                status={
                  isSubmitted
                    ? "submitted"
                    : isStreaming
                      ? "streaming"
                      : status === "error"
                        ? "error"
                        : "ready"
                }
              />
            </PromptInputFooter>
          </PromptInput>
          <p className="mt-2 text-xs text-muted-foreground">
            Press Enter to send. Connected to: {API_URL}
          </p>
        </div>
      </div>
    </div>
  );
}
