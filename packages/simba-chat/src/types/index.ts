import type { CSSProperties, ReactNode } from "react";

// SSE Event types from the backend
export type SSEEventType =
  | "thinking"
  | "tool_start"
  | "tool_end"
  | "tool_call"
  | "content"
  | "error"
  | "done";

export interface SSEEvent {
  type: SSEEventType;
  content?: string;
  message?: string;
  name?: string;
  input?: Record<string, unknown>;
  output?: string;
  id?: string;
  args?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
}

export type ChatStatus = "ready" | "submitted" | "streaming" | "error";

export interface UseSimbaChatOptions {
  apiUrl: string;
  apiKey?: string;
  organizationId?: string;
  collection?: string;
  onError?: (error: Error) => void;
  onMessage?: (message: ChatMessage) => void;
}

export interface UseSimbaChatReturn {
  messages: ChatMessage[];
  status: ChatStatus;
  sendMessage: (content: string) => Promise<void>;
  stop: () => void;
  clear: () => void;
}

export interface SimbaChatProps {
  apiUrl: string;
  apiKey?: string;
  organizationId?: string;
  collection?: string;
  placeholder?: string;
  className?: string;
  style?: CSSProperties;
  onError?: (error: Error) => void;
  onMessage?: (message: ChatMessage) => void;
}

export interface SimbaChatBubbleProps extends SimbaChatProps {
  position?: "bottom-right" | "bottom-left";
  bubbleIcon?: ReactNode;
  defaultOpen?: boolean;
}
