export interface SimbaDoc {
  id: string;
  documents: Document[];
  metadata: Metadata;
}

export interface Metadata {

  filename: string;
  type: string;
  chunk_number?: number;
  page_number?: number;
  parsing_status?: string;
  size?: string;
  loader?: string;
  parser?: string;
  file_path: string;
  folder_path?: string;
  is_folder?: boolean;
  enabled?: boolean;
  uploadedAt?: string;
}

export interface Document {
  id: string;
  content: string;
  metadata: Record<string, any>;
}

