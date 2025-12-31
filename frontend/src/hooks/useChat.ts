import { useCallback, useRef, useState } from "react";
import { API_URL } from "@/lib/constants";

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
  message?: string; // For error events
  name?: string;
  input?: Record<string, unknown>;
  output?: string;
  id?: string;
  args?: string;
}

export interface ToolCall {
  name: string;
  input?: Record<string, unknown>;
  output?: string;
  status: "running" | "completed" | "error";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  tools?: ToolCall[];
  sources?: Array<{
    document_name: string;
    content: string;
    score?: number;
  }>;
  createdAt: Date;
}

export type ChatStatus = "ready" | "submitted" | "streaming" | "error";

interface UseChatOptions {
  onError?: (error: Error) => void;
  onFinish?: (message: ChatMessage) => void;
}

export function useChat(options: UseChatOptions = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [collection, setCollection] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const parseSSEEvent = (line: string): SSEEvent | null => {
    if (!line.startsWith("data: ")) return null;
    try {
      return JSON.parse(line.slice(6)) as SSEEvent;
    } catch {
      return null;
    }
  };

  const parseSourcesFromToolOutput = (
    output: string
  ): ChatMessage["sources"] => {
    // Try to parse RAG tool output to extract sources
    try {
      // The output is markdown formatted, try to extract document references
      const sources: ChatMessage["sources"] = [];
      const lines = output.split("\n");
      let currentSource: {
        document_name: string;
        content: string;
        score?: number;
      } | null = null;

      for (const line of lines) {
        // Look for document headers like "### Document: filename.pdf"
        const docMatch = line.match(/^###?\s*Document:\s*(.+)$/i);
        if (docMatch) {
          if (currentSource) {
            sources.push(currentSource);
          }
          currentSource = {
            document_name: docMatch[1].trim(),
            content: "",
          };
          continue;
        }

        // Look for score/relevance lines
        const scoreMatch = line.match(/Score:\s*([\d.]+)/i);
        if (scoreMatch && currentSource) {
          currentSource.score = parseFloat(scoreMatch[1]);
          continue;
        }

        // Accumulate content
        if (currentSource && line.trim()) {
          currentSource.content += (currentSource.content ? "\n" : "") + line;
        }
      }

      if (currentSource) {
        sources.push(currentSource);
      }

      return sources.length > 0 ? sources : undefined;
    } catch {
      return undefined;
    }
  };

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || status === "streaming") return;

      // Cancel any existing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: content.trim(),
        createdAt: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setStatus("submitted");

      const assistantMessageId = crypto.randomUUID();
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        tools: [],
        createdAt: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      try {
        const response = await fetch(
          `${API_URL}/api/v1/conversations/chat/stream`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content: userMessage.content,
              conversation_id: conversationId,
              collection: collection,
            }),
            signal: abortControllerRef.current.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Update conversation ID from response header or first message
        const newConversationId = response.headers.get("X-Conversation-Id");
        if (newConversationId && !conversationId) {
          setConversationId(newConversationId);
        }

        setStatus("streaming");

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";
        let currentThinking = "";
        let currentContent = "";
        const currentTools: ToolCall[] = [];
        let sources: ChatMessage["sources"] = undefined;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const event = parseSSEEvent(line);
            if (!event) continue;

            switch (event.type) {
              case "thinking":
                setIsThinking(true);
                currentThinking += event.content || "";
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, thinking: currentThinking }
                      : msg
                  )
                );
                break;

              case "tool_start":
                setIsThinking(false);
                const newTool: ToolCall = {
                  name: event.name || "unknown",
                  input: event.input,
                  status: "running",
                };
                currentTools.push(newTool);
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, tools: [...currentTools] }
                      : msg
                  )
                );
                break;

              case "tool_end":
                const toolIndex = currentTools.findIndex(
                  (t) => t.name === event.name && t.status === "running"
                );
                if (toolIndex !== -1) {
                  currentTools[toolIndex] = {
                    ...currentTools[toolIndex],
                    output: event.output,
                    status: "completed",
                  };

                  // Parse sources from RAG tool output
                  if (event.name === "rag" && event.output) {
                    const parsedSources = parseSourcesFromToolOutput(
                      event.output
                    );
                    if (parsedSources) {
                      sources = parsedSources;
                    }
                  }

                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMessageId
                        ? { ...msg, tools: [...currentTools], sources }
                        : msg
                    )
                  );
                }
                break;

              case "content":
                setIsThinking(false);
                currentContent += event.content || "";
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: currentContent }
                      : msg
                  )
                );
                break;

              case "error":
                // Handle error from backend
                const errorMsg = event.message || "An error occurred";
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: errorMsg }
                      : msg
                  )
                );
                options.onError?.(new Error(errorMsg));
                break;

              case "done":
                setStatus("ready");
                setIsThinking(false);
                // Call onFinish with the final message
                const finalMessage: ChatMessage = {
                  id: assistantMessageId,
                  role: "assistant",
                  content: currentContent,
                  thinking: currentThinking || undefined,
                  tools: currentTools.length > 0 ? currentTools : undefined,
                  sources,
                  createdAt: new Date(),
                };
                options.onFinish?.(finalMessage);
                break;
            }
          }
        }
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          setStatus("ready");
          return;
        }

        setStatus("error");
        setIsThinking(false);
        const errorMessage =
          error instanceof Error ? error.message : "An error occurred";

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content:
                    "Sorry, I encountered an error. Please make sure the backend is running.",
                }
              : msg
          )
        );

        options.onError?.(
          error instanceof Error ? error : new Error(errorMessage)
        );
      }
    },
    [conversationId, collection, status, options]
  );

  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("ready");
    setIsThinking(false);
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setStatus("ready");
    setIsThinking(false);
  }, []);

  return {
    messages,
    status,
    conversationId,
    collection,
    setCollection,
    isThinking,
    sendMessage,
    stop,
    clear,
  };
}
