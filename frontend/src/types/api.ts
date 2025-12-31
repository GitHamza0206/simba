// API Response Types

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta?: {
    timestamp: string;
    request_id: string;
  };
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// Document Types
export type DocumentStatus = "pending" | "parsing" | "ready" | "failed";

export interface Document {
  id: string;
  name: string;
  file_path: string;
  mime_type: string;
  size_bytes: number;
  status: DocumentStatus;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Chunk {
  id: string;
  document_id: string;
  content: string;
  metadata: Record<string, unknown>;
  position: number;
  created_at: string;
}

// Conversation Types
export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  sources?: ChunkReference[];
  feedback?: Feedback | null;
  latency_ms?: number;
  created_at: string;
}

export interface ChunkReference {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content: string;
  score: number;
}

export interface Feedback {
  id: string;
  message_id: string;
  rating: number;
  reason?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  external_id?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

// Chat Types
export interface ChatRequest {
  conversation_id?: string;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  sources: ChunkReference[];
}

// Retrieval Types
export interface SearchRequest {
  query: string;
  k?: number;
  filter?: Record<string, unknown>;
}

export interface SearchResult {
  documents: ChunkReference[];
  query: string;
  latency_ms: number;
}
