import { cn } from "../utils/cn";
import { MarkdownContent } from "./MarkdownContent";
import type { ChatMessage as ChatMessageType } from "../types";

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
  className?: string;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ChatMessage({
  message,
  isStreaming,
  className,
}: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "simba-message",
        isUser ? "simba-message-user" : "simba-message-assistant",
        className
      )}
    >
      <div className="simba-message-avatar">
        {isUser ? (
          <svg
            className="simba-message-avatar-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        ) : (
          <svg
            className="simba-message-avatar-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M12 8V4H8" />
            <rect width="16" height="12" x="4" y="8" rx="2" />
            <path d="M2 14h2" />
            <path d="M20 14h2" />
            <path d="M15 13v2" />
            <path d="M9 13v2" />
          </svg>
        )}
      </div>

      <div className="simba-message-content">
        <div className="simba-message-header">
          <span className="simba-message-author">
            {isUser ? "You" : "Assistant"}
          </span>
          <span className="simba-message-time">{formatTime(message.createdAt)}</span>
        </div>

        <div className="simba-message-body">
          {isUser ? (
            <div className="simba-message-bubble">
              <p>{message.content}</p>
            </div>
          ) : message.content ? (
            <MarkdownContent content={message.content} />
          ) : isStreaming ? (
            <span className="simba-message-loading">...</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}
