export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
  state?: any;
  followUpQuestions?: string[];
} 