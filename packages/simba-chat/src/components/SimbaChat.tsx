import { useState } from "react";
import { cn } from "../utils/cn";
import { useSimbaChat } from "../hooks/useSimbaChat";
import { ChatContainer } from "./ChatContainer";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import type { SimbaChatProps } from "../types";

export function SimbaChat({
  apiUrl,
  apiKey,
  organizationId,
  collection,
  placeholder = "Type a message...",
  className,
  style,
  onError,
  onMessage,
}: SimbaChatProps) {
  const [inputValue, setInputValue] = useState("");

  const { messages, status, sendMessage, stop, clear } = useSimbaChat({
    apiUrl,
    apiKey,
    organizationId,
    collection,
    onError,
    onMessage,
  });

  const handleSubmit = () => {
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue("");
    }
  };

  const isStreaming = status === "streaming";
  const lastMessageId = messages[messages.length - 1]?.id;

  return (
    <div className={cn("simba-chat", className)} style={style}>
      <ChatContainer>
        {messages.length === 0 ? (
          <div className="simba-chat-empty">
            <div className="simba-chat-empty-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <p className="simba-chat-empty-text">Start a conversation</p>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              isStreaming={isStreaming && message.id === lastMessageId}
            />
          ))
        )}
      </ChatContainer>

      <div className="simba-chat-footer">
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSubmit}
          onStop={stop}
          status={status}
          placeholder={placeholder}
        />
      </div>
    </div>
  );
}
