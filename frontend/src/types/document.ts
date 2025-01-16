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

  loaderModified?: boolean;
  parserModified?: boolean;

}

export interface DocumentStatsType {
  lastQueried: string;
  totalQueries: number;
  itemsIndexed: number;
  createdAt: string;
} 