import { useState, type ReactNode } from "react";
import { cn } from "../utils/cn";
import { SimbaChat } from "./SimbaChat";
import type { SimbaChatBubbleProps } from "../types";

const DefaultBubbleIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className="simba-bubble-icon-svg"
  >
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const CloseIcon = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    className="simba-bubble-icon-svg"
  >
    <path d="M18 6 6 18" />
    <path d="m6 6 12 12" />
  </svg>
);

export function SimbaChatBubble({
  position = "bottom-right",
  bubbleIcon,
  defaultOpen = false,
  className,
  style,
  ...chatProps
}: SimbaChatBubbleProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div
      className={cn(
        "simba-bubble-wrapper",
        position === "bottom-left"
          ? "simba-bubble-wrapper-left"
          : "simba-bubble-wrapper-right",
        className
      )}
      style={style}
    >
      {isOpen && (
        <div className="simba-bubble-chat">
          <SimbaChat {...chatProps} />
        </div>
      )}

      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="simba-bubble-button"
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {isOpen ? <CloseIcon /> : (bubbleIcon || <DefaultBubbleIcon />)}
      </button>
    </div>
  );
}
