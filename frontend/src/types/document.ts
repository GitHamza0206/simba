export interface DocumentType {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadedAt: string;
  content: string;
  loader?: string;
  loaderModified?: boolean;
}

export interface DocumentStatsType {
  lastQueried: string;
  totalQueries: number;
  itemsIndexed: number;
  createdAt: string;
} 