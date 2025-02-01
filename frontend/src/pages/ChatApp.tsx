import React, { useState, useEffect } from 'react';
import ChatFrame from '@/components/ChatFrame';
import { cn } from "@/lib/utils";
import { MoreVertical, RotateCw } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Message } from '@/types/chat';
import { config } from '@/config';

const STORAGE_KEY = 'chat_messages';

const ChatApp: React.FC = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [messages, setMessages] = useState<Message[]>(() => {
    // Load messages from localStorage on initial render
    const savedMessages = localStorage.getItem(STORAGE_KEY);
    return savedMessages ? JSON.parse(savedMessages) : [];
  });

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  const handleClearMessages = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const handleEndDiscussion = () => {
    handleClearMessages();
    window.parent.postMessage({ type: 'CLOSE_CHAT' }, '*');
  };

  return (
    <div className="p-6 h-full">
      <div className="bg-white shadow-xl flex flex-col h-full rounded-xl">
        <div className="bg-[#0066b2] text-white py-2 px-4 flex items-center justify-between shrink-0 rounded-t-xl">
          <h1 className="text-xl font-semibold">{config.appName}</h1>
          
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger className="hover:bg-[#0077cc] p-1 rounded">
                <MoreVertical className="h-5 w-5" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={handleClearMessages}>
                  Nouvelle discussion
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleEndDiscussion}>
                  Terminer la discussion
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <button 
              onClick={handleClearMessages}
              className="hover:bg-[#0077cc] p-1 rounded"
            >
              <RotateCw className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-hidden">
          <ChatFrame messages={messages} setMessages={setMessages} />
        </div>
      </div>
    </div>
  );
};

export default ChatApp; 