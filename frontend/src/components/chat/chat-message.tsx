"use client";

import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { MarkdownContent } from "./markdown-content";
import { ChatThinking } from "./chat-thinking";
import { ChatSources } from "./chat-sources";
import { ChatStatus } from "./chat-status";
import { ChatLatency } from "./chat-latency";
import { ChatContext } from "./chat-context";
import type { ChatMessage as ChatMessageType } from "@/hooks";

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
  className?: string;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ChatMessage({ message, isStreaming, className }: ChatMessageProps) {
  const isUser = message.role === "user";
  const hasRunningTool = message.tools?.some((t) => t.status === "running");
  const showStatus = isStreaming && hasRunningTool;

  // Get the RAG tool with latency data
  const ragTool = message.tools?.find(
    (t) => t.name === "rag" && t.status === "completed"
  );

  return (
    <div
      className={cn(
        "group flex gap-3 py-3",
        isUser && "flex-row-reverse",
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-muted-foreground"
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div
        className={cn(
          "flex-1 space-y-1 overflow-hidden",
          isUser ? "text-right" : "text-left"
        )}
      >
        {/* Header */}
        <div
          className={cn(
            "flex items-center gap-2 text-xs text-muted-foreground",
            isUser && "flex-row-reverse"
          )}
        >
          <span className="font-medium text-foreground">
            {isUser ? "You" : "Simba"}
          </span>
          <span>{formatTime(message.createdAt)}</span>
          {/* Latency indicator for assistant messages */}
          {!isUser && message.latency && (
            <ChatLatency latency={message.latency} />
          )}
        </div>

        {/* Status indicator (while working) */}
        {showStatus && <ChatStatus tools={message.tools} />}

        {/* Message content - THE MAIN FOCUS */}
        <div className={cn("text-sm", isUser && "text-right")}>
          {isUser ? (
            <div className="inline-block rounded-2xl bg-primary px-4 py-2 text-primary-foreground">
              <p className="whitespace-pre-wrap">{message.content}</p>
            </div>
          ) : message.content ? (
            <MarkdownContent content={message.content} />
          ) : (
            !showStatus && (
              <span className="text-muted-foreground text-xs">...</span>
            )
          )}
        </div>

        {/* Sources as citations (AFTER content) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <ChatSources sources={message.sources} />
        )}

        {/* RAG Context (collapsible full context) */}
        {!isUser && ragTool && <ChatContext tool={ragTool} />}

        {/* Thinking (collapsed, at the end) */}
        {!isUser && message.thinking && (
          <ChatThinking thinking={message.thinking} />
        )}
      </div>
    </div>
  );
}
