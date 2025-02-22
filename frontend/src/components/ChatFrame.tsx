import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, Paperclip } from 'lucide-react';
import ChatMessage from './ChatMessage';
import { Message } from '@/types/chat';
import Thinking from '@/components/Thinking';
import { sendMessage, handleChatStream } from '@/lib/api';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useToast } from "@/hooks/use-toast";

interface ChatFrameProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  onUploadClick: () => void;
}

const ChatFrame: React.FC<ChatFrameProps> = ({ messages, setMessages, onUploadClick }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userTimestamp = Date.now();
    const botTimestamp = userTimestamp + 1;
    
    // Add user message
    const userMessage: Message = {
      id: `user-${userTimestamp}`,
      role: 'user',
      content: inputMessage.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsThinking(true);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await sendMessage(userMessage.content);
      
      // Add assistant message placeholder
      const assistantMessage: Message = {
        id: `assistant-${botTimestamp}`,
        role: 'assistant',
        content: '',
        streaming: true,
        state: {},
        followUpQuestions: []
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setIsThinking(false);

      await handleChatStream(
        response,
        (content, state) => {
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.id === assistantMessage.id) {
              return [
                ...prev.slice(0, -1),
                { 
                  ...lastMessage,
                  content: content ? (lastMessage.content + content) : lastMessage.content,
                  state: state || lastMessage.state,
                  followUpQuestions: state?.followUpQuestions || lastMessage.followUpQuestions
                }
              ];
            }
            return prev;
          });
        },
        () => {
          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage && lastMessage.id === assistantMessage.id) {
              return [
                ...prev.slice(0, -1),
                { ...lastMessage, streaming: false }
              ];
            }
            return prev;
          });
          setIsLoading(false);
        }
      );

    } catch (error) {
      console.error('Error:', error);
      
      // Show error toast
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'An unexpected error occurred',
        variant: "destructive",
        duration: 5000,
      });

      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.',
      }]);
      setIsLoading(false);
      setIsThinking(false);
    }
  };

  const handleFollowUpClick = (question: string) => {
    setInputMessage(question);
    const fakeEvent = { preventDefault: () => {} } as React.FormEvent;
    handleSubmit(fakeEvent);
  };

  return (
    <Card className="h-full flex flex-col">
      <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            isAi={message.role === 'assistant'}
            message={message.content}
            streaming={message.streaming}
            followUpQuestions={message.followUpQuestions}
            onFollowUpClick={handleFollowUpClick}
            state={message.state}
          />
        ))}
        {isThinking && <Thinking />}
        <div ref={messagesEndRef} />
      </CardContent>

      <CardFooter className="p-4 border-t">
        <form onSubmit={handleSubmit} className="flex w-full gap-2">
          <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded-lg border bg-white">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={onUploadClick}
                    className="h-8 w-8 hover:bg-transparent p-0"
                  >
                    <Paperclip className="h-5 w-5 text-gray-500 rotate-45" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Upload document</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type a message..."
              disabled={isLoading}
              className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 px-0"
            />
          </div>
          <Button 
            type="submit" 
            disabled={isLoading || !inputMessage.trim()}
            className="bg-[#0066b2] hover:bg-[#0077cc]"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardFooter>
    </Card>
  );
};

export default ChatFrame; 