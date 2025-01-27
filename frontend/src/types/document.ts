export interface SimbaDoc {
  id: string;
  documents: Document[];
  metadata: Metadata;
}

export interface Metadata {
  file_path: string;
  folder_path?: string;
  is_folder?: boolean;
  enabled?: boolean;
  uploadedAt?: string;
}

export interface Document {
  id: string;
  content: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  metadata: Record<string, any>;
}