"use client";

import dynamic from "next/dynamic";
import "simba-chat/styles.css";
import { useMemo } from "react";
import { getActiveOrgId } from "@/lib/api";
import { useAuth } from "@/providers/auth-provider";

const SimbaChatBubble = dynamic(
  () => import("simba-chat").then((mod) => mod.SimbaChatBubble),
  { ssr: false }
);

export function ChatWidgetWrapper() {
  const showWidget = process.env.NEXT_PUBLIC_SHOW_CHAT_WIDGET === "true";
  const { activeOrganization } = useAuth();
  const organizationId = useMemo(
    () => activeOrganization?.id || getActiveOrgId() || undefined,
    [activeOrganization?.id]
  );

  if (!showWidget) {
    return null;
  }

  return (
    <SimbaChatBubble
      apiUrl={process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
      organizationId={organizationId}
      position="bottom-right"
    />
  );
}
