export interface DocumentType {
  id: string;
  content: string;
  name: string;
  type: string;
  size: string;
  loader: string;
  parser: string;
  uploadedAt: string; 
  file_path: string;
  folder_path?: string;
  is_folder?: boolean;

  loaderModified?: boolean;
  parserModified?: boolean;
}

export interface DocumentStatsType {
  lastQueried: string;
  totalQueries: number;
  itemsIndexed: number;
  createdAt: string;
}

export interface FolderType {
  id: string;
  name: string;
  path: string;
  created_at: string;
  parent_folder?: string;
} 