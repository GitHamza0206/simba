export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
  state?: {
    sources?: Array<{
      file_name: string;
      chunk: string;
      relevance?: number;
      page?: number;
    }>;
    followUpQuestions?: string[];
  };
  followUpQuestions?: string[];
} 