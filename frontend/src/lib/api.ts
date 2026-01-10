import { API_URL } from "./constants";

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  body?: unknown;
  headers?: Record<string, string>;
};

// Storage key for active organization
const ACTIVE_ORG_KEY = "simba_active_org";

// Get active organization ID from localStorage
export function getActiveOrgId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACTIVE_ORG_KEY);
}

// Set active organization ID in localStorage
export function setActiveOrgId(orgId: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(ACTIVE_ORG_KEY, orgId);
  }
}

// Clear active organization ID
export function clearActiveOrgId(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(ACTIVE_ORG_KEY);
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = "GET", body, headers = {} } = options;

    // Build headers with organization context
    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      ...headers,
    };

    // Add organization ID header if available
    const orgId = getActiveOrgId();
    if (orgId) {
      requestHeaders["X-Organization-Id"] = orgId;
    }

    const config: RequestInit = {
      method,
      headers: requestHeaders,
      credentials: "include", // Include cookies for session
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, config);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  get<T>(endpoint: string, headers?: Record<string, string>) {
    return this.request<T>(endpoint, { headers });
  }

  post<T>(endpoint: string, body?: unknown, headers?: Record<string, string>) {
    return this.request<T>(endpoint, { method: "POST", body, headers });
  }

  put<T>(endpoint: string, body?: unknown, headers?: Record<string, string>) {
    return this.request<T>(endpoint, { method: "PUT", body, headers });
  }

  delete<T>(endpoint: string, headers?: Record<string, string>) {
    return this.request<T>(endpoint, { method: "DELETE", headers });
  }

  patch<T>(endpoint: string, body?: unknown, headers?: Record<string, string>) {
    return this.request<T>(endpoint, { method: "PATCH", body, headers });
  }
}

export const api = new ApiClient(API_URL);
