import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import chatbotIcon from "../assets/chatbot-icon.svg";
import FollowUpQuestions from './FollowUpQuestions';
import { Button } from "@/components/ui/button";
import { FileText, Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react';
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
  const [copied, setCopied] = React.useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(cleanMessage);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

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
    <div className="flex flex-col w-full max-w-full group">
      {!isAi && (
        <div className="w-full py-4 flex justify-center">
          <div className="w-full max-w-2xl px-4">
            <div className="flex justify-end">
              <div className="max-w-fit bg-blue-600 text-white rounded-lg px-4 py-3">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkBreaks]}
                  className="prose prose-sm max-w-none break-words text-white prose-headings:text-white prose-strong:text-white prose-a:text-blue-100 hover:prose-a:text-blue-50"
                >
                  {cleanMessage}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {isAi && (
        <div className="w-full py-4 bg-gray-50">
          <div className="w-full max-w-2xl mx-auto px-4">
            <div className="flex">
              <img 
                src={chatbotIcon} 
                alt="Bot" 
                className="w-6 h-6 rounded-full shrink-0 mt-1 mr-3"
              />
              <div className="flex-1">
                <div 
                  className={`overflow-hidden ${
                    isSelected 
                      ? 'text-gray-800' 
                      : 'text-gray-800'
                  }`}
                >
                  <div className="prose prose-sm max-w-none break-words overflow-auto relative">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm, remarkBreaks]}
                      className="prose-pre:bg-gray-100 prose-pre:border prose-pre:border-gray-200 prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded-md"
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
                              className="flex items-center gap-1 h-8 text-blue-700 border-blue-200 hover:bg-blue-50 transition-colors"
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
                    {/* Feedback Buttons Row */}
                    <div className="flex justify-center gap-2 mt-4 mx-auto">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="text-gray-500 hover:bg-gray-100"
                              onClick={copyToClipboard}
                            >
                              {copied ? <Check className="h-5 w-5 text-green-500" /> : <Copy className="h-5 w-5" />}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>{copied ? 'Copied!' : 'Copy message'}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                      <Button variant="ghost" size="icon" className="text-gray-500 hover:bg-gray-100">
                        <ThumbsUp className="h-5 w-5" />
                      </Button>
                      <Button variant="ghost" size="icon" className="text-gray-500 hover:bg-gray-100">
                        <ThumbsDown className="h-5 w-5" />
                      </Button>
                    </div>
                  </div>
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