import * as react_jsx_runtime from 'react/jsx-runtime';
import { CSSProperties, ReactNode } from 'react';

interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    createdAt: Date;
}
type ChatStatus = "ready" | "submitted" | "streaming" | "error";
interface UseSimbaChatOptions {
    apiUrl: string;
    apiKey?: string;
    organizationId?: string;
    collection?: string;
    onError?: (error: Error) => void;
    onMessage?: (message: ChatMessage) => void;
}
interface UseSimbaChatReturn {
    messages: ChatMessage[];
    status: ChatStatus;
    sendMessage: (content: string) => Promise<void>;
    stop: () => void;
    clear: () => void;
}
interface SimbaChatProps {
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
interface SimbaChatBubbleProps extends SimbaChatProps {
    position?: "bottom-right" | "bottom-left";
    bubbleIcon?: ReactNode;
    defaultOpen?: boolean;
}

declare function SimbaChat({ apiUrl, apiKey, organizationId, collection, placeholder, className, style, onError, onMessage, }: SimbaChatProps): react_jsx_runtime.JSX.Element;

declare function SimbaChatBubble({ position, bubbleIcon, defaultOpen, className, style, ...chatProps }: SimbaChatBubbleProps): react_jsx_runtime.JSX.Element;

declare function useSimbaChat(options: UseSimbaChatOptions): UseSimbaChatReturn;

export { type ChatMessage, type ChatStatus, SimbaChat, SimbaChatBubble, type SimbaChatBubbleProps, type SimbaChatProps, type UseSimbaChatOptions, type UseSimbaChatReturn, useSimbaChat };
