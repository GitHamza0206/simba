// src/components/SimbaChat.tsx
import { useState as useState2 } from "react";

// src/utils/cn.ts
import { clsx } from "clsx";
function cn(...inputs) {
  return clsx(inputs);
}

// src/hooks/useSimbaChat.ts
import { useCallback, useRef, useState } from "react";
function useSimbaChat(options) {
  const { apiUrl, apiKey, collection, onError, onMessage } = options;
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("ready");
  const [conversationId, setConversationId] = useState(null);
  const abortControllerRef = useRef(null);
  const parseSSEEvent = (line) => {
    if (!line.startsWith("data: ")) return null;
    try {
      return JSON.parse(line.slice(6));
    } catch {
      return null;
    }
  };
  const sendMessage = useCallback(
    async (content) => {
      if (!content.trim() || status === "streaming") return;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();
      const userMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: content.trim(),
        createdAt: /* @__PURE__ */ new Date()
      };
      setMessages((prev) => [...prev, userMessage]);
      setStatus("submitted");
      const assistantMessageId = crypto.randomUUID();
      const assistantMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        createdAt: /* @__PURE__ */ new Date()
      };
      setMessages((prev) => [...prev, assistantMessage]);
      try {
        const response = await fetch(
          `${apiUrl}/api/v1/conversations/chat/stream`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${apiKey}`
            },
            body: JSON.stringify({
              content: userMessage.content,
              conversation_id: conversationId,
              collection
            }),
            signal: abortControllerRef.current.signal
          }
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
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
                setMessages(
                  (prev) => prev.map(
                    (msg) => msg.id === assistantMessageId ? { ...msg, content: currentContent } : msg
                  )
                );
                break;
              case "error":
                const errorMsg = event.message || "An error occurred";
                setMessages(
                  (prev) => prev.map(
                    (msg) => msg.id === assistantMessageId ? { ...msg, content: errorMsg } : msg
                  )
                );
                onError?.(new Error(errorMsg));
                break;
              case "done":
                setStatus("ready");
                const finalMessage = {
                  id: assistantMessageId,
                  role: "assistant",
                  content: currentContent,
                  createdAt: /* @__PURE__ */ new Date()
                };
                onMessage?.(finalMessage);
                break;
            }
          }
        }
      } catch (error) {
        if (error.name === "AbortError") {
          setStatus("ready");
          return;
        }
        setStatus("error");
        const errorMessage = error instanceof Error ? error.message : "An error occurred";
        setMessages(
          (prev) => prev.map(
            (msg) => msg.id === assistantMessageId ? {
              ...msg,
              content: "Sorry, an error occurred. Please try again."
            } : msg
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
    clear
  };
}

// src/components/ChatContainer.tsx
import { useRef as useRef2, useEffect } from "react";
import { jsx } from "react/jsx-runtime";
function ChatContainer({
  children,
  className,
  autoScroll = true
}) {
  const scrollRef = useRef2(null);
  const isAtBottomRef = useRef2(true);
  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };
  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    isAtBottomRef.current = distanceFromBottom < 100;
  };
  useEffect(() => {
    if (autoScroll && isAtBottomRef.current) {
      scrollToBottom();
    }
  }, [children, autoScroll]);
  return /* @__PURE__ */ jsx(
    "div",
    {
      ref: scrollRef,
      className: cn("simba-chat-container", className),
      onScroll: handleScroll,
      children: /* @__PURE__ */ jsx("div", { className: "simba-chat-messages", children })
    }
  );
}

// src/components/MarkdownContent.tsx
import ReactMarkdown from "react-markdown";
import { jsx as jsx2 } from "react/jsx-runtime";
function MarkdownContent({ content, className }) {
  return /* @__PURE__ */ jsx2("div", { className: cn("simba-markdown", className), children: /* @__PURE__ */ jsx2(
    ReactMarkdown,
    {
      components: {
        p: ({ children }) => /* @__PURE__ */ jsx2("p", { className: "simba-markdown-p", children }),
        a: ({ href, children }) => /* @__PURE__ */ jsx2(
          "a",
          {
            href,
            target: "_blank",
            rel: "noopener noreferrer",
            className: "simba-markdown-link",
            children
          }
        ),
        ul: ({ children }) => /* @__PURE__ */ jsx2("ul", { className: "simba-markdown-ul", children }),
        ol: ({ children }) => /* @__PURE__ */ jsx2("ol", { className: "simba-markdown-ol", children }),
        li: ({ children }) => /* @__PURE__ */ jsx2("li", { className: "simba-markdown-li", children }),
        code: ({ children, className: className2 }) => {
          const isInline = !className2;
          return isInline ? /* @__PURE__ */ jsx2("code", { className: "simba-markdown-code-inline", children }) : /* @__PURE__ */ jsx2("code", { className: "simba-markdown-code-block", children });
        },
        pre: ({ children }) => /* @__PURE__ */ jsx2("pre", { className: "simba-markdown-pre", children }),
        blockquote: ({ children }) => /* @__PURE__ */ jsx2("blockquote", { className: "simba-markdown-blockquote", children })
      },
      children: content
    }
  ) });
}

// src/components/ChatMessage.tsx
import { jsx as jsx3, jsxs } from "react/jsx-runtime";
function formatTime(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function ChatMessage({
  message,
  isStreaming,
  className
}) {
  const isUser = message.role === "user";
  return /* @__PURE__ */ jsxs(
    "div",
    {
      className: cn(
        "simba-message",
        isUser ? "simba-message-user" : "simba-message-assistant",
        className
      ),
      children: [
        /* @__PURE__ */ jsx3("div", { className: "simba-message-avatar", children: isUser ? /* @__PURE__ */ jsxs(
          "svg",
          {
            className: "simba-message-avatar-icon",
            viewBox: "0 0 24 24",
            fill: "none",
            stroke: "currentColor",
            strokeWidth: "2",
            children: [
              /* @__PURE__ */ jsx3("path", { d: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" }),
              /* @__PURE__ */ jsx3("circle", { cx: "12", cy: "7", r: "4" })
            ]
          }
        ) : /* @__PURE__ */ jsxs(
          "svg",
          {
            className: "simba-message-avatar-icon",
            viewBox: "0 0 24 24",
            fill: "none",
            stroke: "currentColor",
            strokeWidth: "2",
            children: [
              /* @__PURE__ */ jsx3("path", { d: "M12 8V4H8" }),
              /* @__PURE__ */ jsx3("rect", { width: "16", height: "12", x: "4", y: "8", rx: "2" }),
              /* @__PURE__ */ jsx3("path", { d: "M2 14h2" }),
              /* @__PURE__ */ jsx3("path", { d: "M20 14h2" }),
              /* @__PURE__ */ jsx3("path", { d: "M15 13v2" }),
              /* @__PURE__ */ jsx3("path", { d: "M9 13v2" })
            ]
          }
        ) }),
        /* @__PURE__ */ jsxs("div", { className: "simba-message-content", children: [
          /* @__PURE__ */ jsxs("div", { className: "simba-message-header", children: [
            /* @__PURE__ */ jsx3("span", { className: "simba-message-author", children: isUser ? "You" : "Assistant" }),
            /* @__PURE__ */ jsx3("span", { className: "simba-message-time", children: formatTime(message.createdAt) })
          ] }),
          /* @__PURE__ */ jsx3("div", { className: "simba-message-body", children: isUser ? /* @__PURE__ */ jsx3("div", { className: "simba-message-bubble", children: /* @__PURE__ */ jsx3("p", { children: message.content }) }) : message.content ? /* @__PURE__ */ jsx3(MarkdownContent, { content: message.content }) : isStreaming ? /* @__PURE__ */ jsx3("span", { className: "simba-message-loading", children: "..." }) : null })
        ] })
      ]
    }
  );
}

// src/components/ChatInput.tsx
import {
  useRef as useRef3,
  useEffect as useEffect2
} from "react";
import { jsx as jsx4, jsxs as jsxs2 } from "react/jsx-runtime";
function ChatInput({
  value,
  onChange,
  onSubmit,
  onStop,
  status = "ready",
  placeholder = "Type a message...",
  disabled = false,
  className
}) {
  const textareaRef = useRef3(null);
  const isLoading = status === "submitted" || status === "streaming";
  const isDisabled = disabled || status === "submitted";
  useEffect2(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [value]);
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isDisabled && value.trim()) {
        onSubmit();
      }
    }
  };
  const handleChange = (e) => {
    onChange(e.target.value);
  };
  return /* @__PURE__ */ jsxs2("div", { className: cn("simba-input-container", className), children: [
    /* @__PURE__ */ jsx4(
      "textarea",
      {
        ref: textareaRef,
        value,
        onChange: handleChange,
        onKeyDown: handleKeyDown,
        placeholder,
        disabled: isDisabled,
        rows: 1,
        className: "simba-input-textarea"
      }
    ),
    status === "streaming" && onStop ? /* @__PURE__ */ jsx4(
      "button",
      {
        type: "button",
        onClick: onStop,
        className: "simba-input-button simba-input-button-stop",
        "aria-label": "Stop",
        children: /* @__PURE__ */ jsx4("svg", { viewBox: "0 0 24 24", fill: "currentColor", className: "simba-input-icon", children: /* @__PURE__ */ jsx4("rect", { x: "6", y: "6", width: "12", height: "12", rx: "2" }) })
      }
    ) : /* @__PURE__ */ jsx4(
      "button",
      {
        type: "button",
        onClick: onSubmit,
        disabled: isDisabled || !value.trim(),
        className: "simba-input-button simba-input-button-send",
        "aria-label": "Send",
        children: status === "submitted" ? /* @__PURE__ */ jsx4(
          "svg",
          {
            viewBox: "0 0 24 24",
            fill: "none",
            stroke: "currentColor",
            strokeWidth: "2",
            className: "simba-input-icon simba-input-icon-loading",
            children: /* @__PURE__ */ jsx4("path", { d: "M21 12a9 9 0 1 1-6.219-8.56" })
          }
        ) : /* @__PURE__ */ jsxs2(
          "svg",
          {
            viewBox: "0 0 24 24",
            fill: "none",
            stroke: "currentColor",
            strokeWidth: "2",
            className: "simba-input-icon",
            children: [
              /* @__PURE__ */ jsx4("path", { d: "m22 2-7 20-4-9-9-4Z" }),
              /* @__PURE__ */ jsx4("path", { d: "M22 2 11 13" })
            ]
          }
        )
      }
    )
  ] });
}

// src/components/SimbaChat.tsx
import { jsx as jsx5, jsxs as jsxs3 } from "react/jsx-runtime";
function SimbaChat({
  apiUrl,
  apiKey,
  collection,
  placeholder = "Type a message...",
  className,
  style,
  onError,
  onMessage
}) {
  const [inputValue, setInputValue] = useState2("");
  const { messages, status, sendMessage, stop, clear } = useSimbaChat({
    apiUrl,
    apiKey,
    collection,
    onError,
    onMessage
  });
  const handleSubmit = () => {
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue("");
    }
  };
  const isStreaming = status === "streaming";
  const lastMessageId = messages[messages.length - 1]?.id;
  return /* @__PURE__ */ jsxs3("div", { className: cn("simba-chat", className), style, children: [
    /* @__PURE__ */ jsx5(ChatContainer, { children: messages.length === 0 ? /* @__PURE__ */ jsxs3("div", { className: "simba-chat-empty", children: [
      /* @__PURE__ */ jsx5("div", { className: "simba-chat-empty-icon", children: /* @__PURE__ */ jsx5(
        "svg",
        {
          viewBox: "0 0 24 24",
          fill: "none",
          stroke: "currentColor",
          strokeWidth: "1.5",
          children: /* @__PURE__ */ jsx5("path", { d: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" })
        }
      ) }),
      /* @__PURE__ */ jsx5("p", { className: "simba-chat-empty-text", children: "Start a conversation" })
    ] }) : messages.map((message) => /* @__PURE__ */ jsx5(
      ChatMessage,
      {
        message,
        isStreaming: isStreaming && message.id === lastMessageId
      },
      message.id
    )) }),
    /* @__PURE__ */ jsx5("div", { className: "simba-chat-footer", children: /* @__PURE__ */ jsx5(
      ChatInput,
      {
        value: inputValue,
        onChange: setInputValue,
        onSubmit: handleSubmit,
        onStop: stop,
        status,
        placeholder
      }
    ) })
  ] });
}

// src/components/SimbaChatBubble.tsx
import { useState as useState3 } from "react";
import { jsx as jsx6, jsxs as jsxs4 } from "react/jsx-runtime";
var DefaultBubbleIcon = () => /* @__PURE__ */ jsx6(
  "svg",
  {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    className: "simba-bubble-icon-svg",
    children: /* @__PURE__ */ jsx6("path", { d: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" })
  }
);
var CloseIcon = () => /* @__PURE__ */ jsxs4(
  "svg",
  {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    className: "simba-bubble-icon-svg",
    children: [
      /* @__PURE__ */ jsx6("path", { d: "M18 6 6 18" }),
      /* @__PURE__ */ jsx6("path", { d: "m6 6 12 12" })
    ]
  }
);
function SimbaChatBubble({
  position = "bottom-right",
  bubbleIcon,
  defaultOpen = false,
  className,
  style,
  ...chatProps
}) {
  const [isOpen, setIsOpen] = useState3(defaultOpen);
  return /* @__PURE__ */ jsxs4(
    "div",
    {
      className: cn(
        "simba-bubble-wrapper",
        position === "bottom-left" ? "simba-bubble-wrapper-left" : "simba-bubble-wrapper-right",
        className
      ),
      style,
      children: [
        isOpen && /* @__PURE__ */ jsx6("div", { className: "simba-bubble-chat", children: /* @__PURE__ */ jsx6(SimbaChat, { ...chatProps }) }),
        /* @__PURE__ */ jsx6(
          "button",
          {
            type: "button",
            onClick: () => setIsOpen(!isOpen),
            className: "simba-bubble-button",
            "aria-label": isOpen ? "Close chat" : "Open chat",
            children: isOpen ? /* @__PURE__ */ jsx6(CloseIcon, {}) : bubbleIcon || /* @__PURE__ */ jsx6(DefaultBubbleIcon, {})
          }
        )
      ]
    }
  );
}
export {
  SimbaChat,
  SimbaChatBubble,
  useSimbaChat
};
//# sourceMappingURL=index.js.map