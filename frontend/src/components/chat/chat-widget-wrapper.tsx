"use client";

import dynamic from "next/dynamic";
import "simba-chat/styles.css";

const SimbaChatBubble = dynamic(
  () => import("simba-chat").then((mod) => mod.SimbaChatBubble),
  { ssr: false }
);

export function ChatWidgetWrapper() {
  const showWidget = process.env.NEXT_PUBLIC_SHOW_CHAT_WIDGET === "true";

  if (!showWidget) {
    return null;
  }

  return (
    <SimbaChatBubble
      apiUrl={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
      position="bottom-right"
    />
  );
}
