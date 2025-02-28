import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import chatbotIcon from "../assets/chatbot-icon.svg";
import FollowUpQuestions from './FollowUpQuestions';
import { Button } from "@/components/ui/button";
import { FileText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ChatMessageProps {
  isAi: boolean;
  message: string;
  streaming?: boolean;
  followUpQuestions?: string[];
  onFollowUpClick?: (question: string) => void;
  onSourceClick?: () => void;
  isSelected?: boolean;
  state?: {
    sources?: Array<{ file_name: string }>;
  };
}

const ChatMessage: React.FC<ChatMessageProps> = ({ 
  isAi, 
  message, 
  streaming,
  followUpQuestions = [],
  onFollowUpClick,
  state,
  onSourceClick,
  isSelected = false
}) => {
  // Filter out status messages
  const cleanMessage = message.replace(
    /\{"status":\s*"end",\s*"node":\s*"generate",\s*"details":\s*"Node stream ended"\}/g, 
    ''
  ).trim();

  // Don't render if message is empty after cleaning
  if (!cleanMessage) {
    return null;
  }

  const hasSources = isAi && state?.sources && state.sources.length > 0;
  const sourceCount = hasSources ? state?.sources?.length : 0;

  return (
    <div className="flex flex-col max-w-full">
      {!isAi && (
        <div className="flex justify-end w-full">
          <div className="rounded-lg p-4 bg-[#0066b2] text-white whitespace-pre-line max-w-[85%] overflow-hidden break-words">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkBreaks]}
              className="prose prose-sm max-w-none break-words text-white prose-headings:text-white prose-strong:text-white"
            >
              {cleanMessage}
            </ReactMarkdown>
          </div>
        </div>
      )}
      
      {isAi && (
        <div className="flex flex-col w-full">
          <div className="flex items-start gap-2 max-w-full">
            <img 
              src={chatbotIcon} 
              alt="Bot" 
              className="w-8 h-8 rounded-full shrink-0 mt-1"
            />
            <div className="flex-1 min-w-0 max-w-full">
              <div className={`rounded-lg p-4 bg-white border overflow-hidden ${isSelected ? 'border-blue-400 shadow-sm' : ''}`}>
                <div className="prose prose-sm max-w-none break-words overflow-auto">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkBreaks]}
                  >
                    {cleanMessage}
                  </ReactMarkdown>
                </div>
                
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  {hasSources && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={onSourceClick}
                            className="flex items-center gap-1 h-8"
                          >
                            <FileText className="h-3.5 w-3.5" />
                            <span>Sources ({sourceCount})</span>
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>View source documents</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                  
                  {followUpQuestions && followUpQuestions.length > 0 && (
                    <div className="w-full mt-2">
                      <FollowUpQuestions 
                        questions={followUpQuestions}
                        onQuestionClick={onFollowUpClick}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMessage;