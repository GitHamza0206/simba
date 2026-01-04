import { useCallback, useRef, useState } from "react";
import type {
  ChatMessage,
  ChatStatus,
  SSEEvent,
  UseSimbaChatOptions,
  UseSimbaChatReturn,
} from "../types";

export function useSimbaChat(options: UseSimbaChatOptions): UseSimbaChatReturn {
  const { apiUrl, apiKey, collection, onError, onMessage } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<ChatStatus>("ready");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const parseSSEEvent = (line: string): SSEEvent | null => {
    if (!line.startsWith("data: ")) return null;
    try {
      return JSON.parse(line.slice(6)) as SSEEvent;
    } catch {
      return null;
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
        createdAt: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      try {
        const response = await fetch(
          `${apiUrl}/api/v1/conversations/chat/stream`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${apiKey}`,
            },
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
        if (newConversationId && !conversationId) {
          setConversationId(newConversationId);
        }

        setStatus("streaming");

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";
        let currentContent = "";

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
              case "content":
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
                const errorMsg = event.message || "An error occurred";
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: errorMsg }
                      : msg
                  )
                );
                onError?.(new Error(errorMsg));
                break;

              case "done":
                setStatus("ready");
                const finalMessage: ChatMessage = {
                  id: assistantMessageId,
                  role: "assistant",
                  content: currentContent,
                  createdAt: new Date(),
                };
                onMessage?.(finalMessage);
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
        const errorMessage =
          error instanceof Error ? error.message : "An error occurred";

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: "Sorry, an error occurred. Please try again.",
                }
              : msg
          )
        );

        onError?.(error instanceof Error ? error : new Error(errorMessage));
      }
    },
    [apiUrl, apiKey, collection, conversationId, status, onError, onMessage]
  );

  const stop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("ready");
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setStatus("ready");
  }, []);

  return {
    messages,
    status,
    sendMessage,
    stop,
    clear,
  };
}
