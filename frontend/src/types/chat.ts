export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
  state?: {
    sources?: Array<{
      file_name: string;
      content?: string;
      page?: number;
      relevance?: number;
    }>;
    followUpQuestions?: string[];
  };
  followUpQuestions?: string[];
} 