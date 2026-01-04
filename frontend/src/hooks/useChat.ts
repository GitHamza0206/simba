import { useCallback, useEffect, useRef, useState } from "react";
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

export interface LatencyBreakdown {
  // Retrieval latency
  embedding_ms?: number;
  search_ms?: number;
  rerank_ms?: number;
  // Response latency
  ttft_ms?: number; // Time to first token
  generation_ms?: number; // LLM generation time
  total_ms?: number;
  // Token counts
  input_tokens?: number;
  output_tokens?: number;
  reasoning_tokens?: number;
}

export interface SSEEvent {
  type: SSEEventType;
  content?: string;
  message?: string; // For error events
  name?: string;
  input?: Record<string, unknown>;
  output?: string;
  latency?: LatencyBreakdown; // Tool latency breakdown
  response_latency?: LatencyBreakdown; // Response latency (in done event)
  id?: string;
  args?: string;
}

export interface ToolCall {
  name: string;
  input?: Record<string, unknown>;
  output?: string;
  status: "running" | "completed" | "error";
  latency?: LatencyBreakdown;
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
  latency?: {
    retrieval?: LatencyBreakdown;
    response?: LatencyBreakdown;
  };
  createdAt: Date;
}

export type ChatStatus = "ready" | "submitted" | "streaming" | "error";

interface UseChatOptions {
  initialConversationId?: string | null;
  onError?: (error: Error) => void;
  onFinish?: (message: ChatMessage) => void;
  onConversationChange?: (conversationId: string | null) => void;
}

export function useChat(options: UseChatOptions = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const [conversationId, setConversationId] = useState<string | null>(
    options.initialConversationId ?? null
  );
  const [collection, setCollection] = useState<string | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const hasLoadedRef = useRef(false);

  // Load conversation history from backend
  const loadConversation = useCallback(async (convId: string) => {
    setIsLoadingHistory(true);
    try {
      const response = await fetch(
        `${API_URL}/api/v1/conversations/${convId}/messages`
      );
      if (!response.ok) {
        if (response.status === 404) {
          // Conversation not found, clear it
          setConversationId(null);
          options.onConversationChange?.(null);
          return;
        }
        throw new Error(`Failed to load conversation: ${response.status}`);
      }
      const data = await response.json();

      // Convert backend messages to ChatMessage format
      const loadedMessages: ChatMessage[] = data
        .filter((msg: { role: string }) => msg.role === "user" || msg.role === "assistant")
        .map((msg: { id?: string; role: "user" | "assistant"; content: string }) => ({
          id: msg.id || crypto.randomUUID(),
          role: msg.role,
          content: msg.content,
          createdAt: new Date(),
        }));

      setMessages(loadedMessages);
    } catch (error) {
      console.error("Failed to load conversation:", error);
      options.onError?.(error instanceof Error ? error : new Error("Failed to load conversation"));
    } finally {
      setIsLoadingHistory(false);
    }
  }, [options]);

  // Load conversation only on initial mount if initialConversationId is provided
  useEffect(() => {
    if (options.initialConversationId && !hasLoadedRef.current) {
      hasLoadedRef.current = true;
      loadConversation(options.initialConversationId);
    }
  }, [options.initialConversationId, loadConversation]);

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

        // Update conversation ID from response header
        const newConversationId = response.headers.get("X-Conversation-Id");
        if (newConversationId && newConversationId !== conversationId) {
          setConversationId(newConversationId);
          // Mark as loaded so we don't try to reload our own conversation
          hasLoadedRef.current = true;
          options.onConversationChange?.(newConversationId);
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
        let retrievalLatency: LatencyBreakdown | undefined = undefined;
        let responseLatency: LatencyBreakdown | undefined = undefined;

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
                    latency: event.latency,
                  };

                  // Parse sources from RAG tool output
                  if (event.name === "rag" && event.output) {
                    const parsedSources = parseSourcesFromToolOutput(
                      event.output
                    );
                    if (parsedSources) {
                      sources = parsedSources;
                    }
                    // Capture retrieval latency from RAG tool
                    if (event.latency) {
                      retrievalLatency = event.latency;
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
                // Capture response latency from done event
                if (event.response_latency) {
                  responseLatency = event.response_latency;
                }
                // Build latency object if we have any data
                const latencyData =
                  retrievalLatency || responseLatency
                    ? {
                        retrieval: retrievalLatency,
                        response: responseLatency,
                      }
                    : undefined;
                // Call onFinish with the final message
                const finalMessage: ChatMessage = {
                  id: assistantMessageId,
                  role: "assistant",
                  content: currentContent,
                  thinking: currentThinking || undefined,
                  tools: currentTools.length > 0 ? currentTools : undefined,
                  sources,
                  latency: latencyData,
                  createdAt: new Date(),
                };
                // Update message with final latency data
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, latency: latencyData }
                      : msg
                  )
                );
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
    hasLoadedRef.current = false;
    options.onConversationChange?.(null);
  }, [options]);

  return {
    messages,
    status,
    conversationId,
    collection,
    setCollection,
    isThinking,
    isLoadingHistory,
    sendMessage,
    stop,
    clear,
  };
}
