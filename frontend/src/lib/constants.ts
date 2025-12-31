export const APP_NAME = "Simba";
export const APP_DESCRIPTION = "AI-powered customer service assistant";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export const ROUTES = {
  HOME: "/",
  PLAYGROUND: "/playground",
  DOCUMENTS: "/documents",
  CONVERSATIONS: "/conversations",
  ANALYTICS: "/analytics",
  SETTINGS: "/settings",
} as const;

export const API_ROUTES = {
  COLLECTIONS: "/api/v1/collections",
  DOCUMENTS: "/api/v1/documents",
  CONVERSATIONS: "/api/v1/conversations",
  CHAT: "/api/v1/chat",
  RETRIEVAL: "/api/v1/retrieval",
  HEALTH: "/api/v1/health",
  ANALYTICS: "/api/v1/analytics",
} as const;
