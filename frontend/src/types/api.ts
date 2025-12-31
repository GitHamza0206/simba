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

export interface ListResponse<T> {
  items: T[];
  total: number;
}

// Collection Types
export interface Collection {
  id: string;
  name: string;
  description: string | null;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface CollectionCreate {
  name: string;
  description?: string;
}

// Document Types
export type DocumentStatus = "pending" | "processing" | "ready" | "failed";

export interface Document {
  id: string;
  name: string;
  collection_id: string;
  collection_name: string;
  status: DocumentStatus;
  size_bytes: number;
  mime_type: string;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  id: string;
  name: string;
  status: string;
  message: string;
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

// Analytics Types
export interface MetricValue {
  value: number;
  change: number;
  period: string;
}

export interface AnalyticsOverview {
  total_conversations: MetricValue;
  total_messages: MetricValue;
  avg_response_time_ms: MetricValue;
  resolution_rate: MetricValue;
  user_satisfaction: MetricValue;
}

export interface EvalMetrics {
  relevance_score: number;
  accuracy_score: number;
  completeness_score: number;
  citation_score: number;
}

export interface DailyStats {
  date: string;
  conversations: number;
  messages: number;
  avg_response_time_ms: number;
}

// Conversation List Types (from backend)
export interface ConversationListItem {
  id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}
