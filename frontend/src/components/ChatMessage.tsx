import React, { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import chatbotIcon from "../assets/chatbot-icon.svg";
import FollowUpQuestions from './FollowUpQuestions';
import { Button } from "@/components/ui/button";
import { Copy, Check, Info, ChevronDown } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

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
  const [showFollowUps, setShowFollowUps] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const markdownRef = useRef<HTMLDivElement>(null);

  const copyToClipboard = async () => {
    if (markdownRef.current) {
      try {
        await navigator.clipboard.writeText(markdownRef.current.innerText);
        setIsCopied(true);
        setTimeout(() => setIsCopied(false), 2000);
      } catch (err) {
        console.error('无法复制文本: ', err);
      }
    }
  };

  const cleanMessage = message.replace(/<br\s*[/]?>/gi, '\n');
  const sourceCount = state?.sources?.length || 0;

  if (!cleanMessage && !(isAi && streaming)) {
    return null;
  }

  return (
    <div className={cn("flex w-full my-2", isAi ? "justify-start" : "justify-end")}>
      <div className={cn(
        "max-w-[80%] p-3 rounded-lg text-sm md:text-base",
        isAi 
          ? "bg-gray-100 text-gray-800 rounded-tl-none shadow-sm text-left"
          : "bg-blue-600 text-white rounded-br-none shadow-md text-right"
      )}>
        {isAi && (
          <div className="flex items-center mb-2">
            <img src={chatbotIcon} alt="AI Icon" className="w-6 h-6 mr-2 rounded-full border border-gray-200" />
            <span className="font-semibold text-gray-700">助理</span>
          </div>
        )}
        <div className="markdown-content" >
          <div className="prose prose-sm max-w-none" ref={markdownRef}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkBreaks]}
              className="prose-pre:bg-gray-100 prose-pre:border prose-pre:border-gray-200 prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1 prose-code:py-0.5 prose-code:rounded-md"
            >
              {cleanMessage}
            </ReactMarkdown>
          </div>

          {isAi && (
            <div className="flex items-center gap-1 mt-2">
              <TooltipProvider delayDuration={200}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-7 w-7 text-gray-500 hover:text-gray-700" onClick={copyToClipboard}>
                      {isCopied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">
                    {isCopied ? '已复制!' : '复制'}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {sourceCount > 0 && onSourceClick && (
                <TooltipProvider delayDuration={200}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className={`h-7 w-7 text-gray-500 hover:text-gray-700 ${isSelected ? 'bg-blue-100 text-blue-600' : ''}`}
                        onClick={onSourceClick}
                      >
                        <Info className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="text-xs">
                      查看来源 ({sourceCount})
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </div>
          )}
        </div>
      </div>
      {isAi && followUpQuestions.length > 0 && (
        <div className={cn("mt-3", isAi ? "pl-10" : "pr-10")}>
          <Button 
            variant="outline"
            size="sm"
            className="text-xs h-7 px-2 py-1"
            onClick={() => setShowFollowUps(!showFollowUps)}
          >
            {showFollowUps ? '隐藏建议' : '显示建议'}
            <ChevronDown className={`h-3 w-3 ml-1 transition-transform duration-200 ${showFollowUps ? 'rotate-180' : ''}`} />
          </Button>
          {showFollowUps && (
            <FollowUpQuestions 
              questions={followUpQuestions} 
              onQuestionClick={onFollowUpClick} 
              className="mt-2"
            />
          )}
        </div>
      )}
    </div>
  );
};

export default ChatMessage;