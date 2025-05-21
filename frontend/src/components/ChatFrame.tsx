import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send, X, Loader2, MessageSquare } from 'lucide-react';
import ChatMessage from './ChatMessage';
import { Message } from '@/types/chat';
import Thinking from '@/components/Thinking';
import { sendMessage, handleChatStream } from '@/lib/api';
import { useToast } from "@/hooks/use-toast";
import SourcePanel from './SourcePanel';
import { motion, AnimatePresence } from 'framer-motion';
import { config } from '@/config';

interface ChatFrameProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}

const ChatFrame: React.FC<ChatFrameProps> = ({ messages, setMessages }) => {
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [sourcePanelOpen, setSourcePanelOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input on load
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  // Close source panel when no message is selected
  useEffect(() => {
    if (!selectedMessage) {
      setSourcePanelOpen(false);
    }
  }, [selectedMessage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    // Close source panel when submitting a new message
    setSelectedMessage(null);
    
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
        title: "错误",
        description: error instanceof Error ? error.message : '发生意外错误',
        variant: "destructive",
        duration: 5000,
      });

      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '抱歉，出现了一些问题。请再试一次。',
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

  const handleSourceClick = (message: Message) => {
    if (message.role === 'assistant' && (message.state?.sources?.length ?? 0) > 0) {
      setSelectedMessage(message);
      setSourcePanelOpen(true);
    }
  };

  const closeSourcePanel = () => {
    setSourcePanelOpen(false);
    setSelectedMessage(null);
  };

  return (
    <div className="h-full w-full flex overflow-hidden">
      {/* Chat panel */}
      <div className="h-full flex-grow overflow-hidden">
        <Card className="h-full flex flex-col rounded-none border-l-0 border-t-0 border-b-0 border-r-0 shadow-none">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-4 space-y-4 opacity-70">
              <motion.div 
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center"
              >
                <MessageSquare className="h-8 w-8 text-blue-500" />
              </motion.div>
              <div className="text-center max-w-md space-y-2">
                <h3 className="text-lg font-medium">欢迎使用 {config.appName}</h3>
                <p className="text-sm text-muted-foreground">
                  提问、获取见解或上传文档进行分析。
                </p>
              </div>
            </div>
          ) : (
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-8 pt-6 flex flex-col items-center">
              <AnimatePresence initial={false}>
                {messages.map((message, idx) => {
                  // Determine margin based on previous message
                  let marginClass = '';
                  if (idx === 0) {
                    marginClass = '';
                  } else {
                    const prevRole = messages[idx - 1].role;
                    if (prevRole !== message.role) {
                      marginClass = 'mt-6'; // Larger margin between different types
                    } else {
                      marginClass = 'mt-2'; // Standard margin between same types
                    }
                  }
                  return (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className={marginClass}
                    >
                      <ChatMessage
                        isAi={message.role === 'assistant'}
                        message={message.content}
                        streaming={message.streaming}
                        followUpQuestions={message.followUpQuestions}
                        onFollowUpClick={handleFollowUpClick}
                        state={message.state}
                        onSourceClick={() => handleSourceClick(message)}
                        isSelected={selectedMessage?.id === message.id}
                      />
                    </motion.div>
                  );
                })}
              </AnimatePresence>
              {isThinking && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <Thinking />
                </motion.div>
              )}
              <div ref={messagesEndRef} />
            </CardContent>
          )}

          <CardFooter className="p-4 border-t bg-white">
            <form onSubmit={handleSubmit} className="w-full flex justify-center">
              <div className="w-full max-w-3xl flex items-center gap-2 px-4 py-2 rounded-full bg-white shadow-lg border border-gray-100">
                <Input
                  ref={inputRef}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="提出一个问题"
                  disabled={isLoading}
                  className="flex-1 border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 px-2 py-1 text-base placeholder:text-gray-400"
                />
                <Button
                  type="submit"
                  disabled={isLoading || !inputMessage.trim()}
                  className="h-10 w-10 rounded-full flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white shadow-md transition-all duration-200"
                >
                  {isLoading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </Button>
              </div>
            </form>
          </CardFooter>
        </Card>
      </div>

      {/* Source Panel - Only displayed when open */}
      <AnimatePresence>
        {sourcePanelOpen && selectedMessage && (
          <motion.div 
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="h-full w-[300px] sm:w-[320px] md:w-[380px] border-l flex flex-col bg-white overflow-hidden shrink-0 shadow-md"
          >
            <div className="flex justify-between items-center p-3 border-b bg-gray-50">
              <h3 className="font-medium text-sm truncate pr-2">来源</h3>
              <Button 
                variant="ghost" 
                size="icon" 
                onClick={closeSourcePanel} 
                className="h-8 w-8 rounded-full hover:bg-gray-200"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-hidden">
              <SourcePanel message={selectedMessage} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ChatFrame; 