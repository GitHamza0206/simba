import React, { useState, useEffect } from 'react';
import ChatFrame from '@/components/ChatFrame';
import { MoreVertical, RotateCw } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Message } from '@/types/chat';
import { config } from '@/config';
import { FileUploadModal } from '@/components/DocumentManagement/FileUploadModal';
import { ingestionApi } from '@/lib/ingestion_api';
import { useToast } from '@/hooks/use-toast';
import { Toaster } from "@/components/ui/toaster";

const STORAGE_KEY = 'chat_messages';

const ChatApp: React.FC = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [messages, setMessages] = useState<Message[]>(() => {
    // Load messages from localStorage on initial render
    const savedMessages = localStorage.getItem(STORAGE_KEY);
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const { toast } = useToast();

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

  const handleChatUpload = async (files: FileList) => {
    try {
      await ingestionApi.uploadDocuments(Array.from(files));
      setIsUploadModalOpen(false);

      // Show toast in chat interface
      toast({
        title: "✅ Upload Successful",
        description: "Your documents have been uploaded. Go to KMS to process them.",
        className: "bg-green-50 text-green-900 border-green-200",
        duration: 5000
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to upload files",
        variant: "destructive",
      });
    }
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
              onClick={() => {
                handleClearMessages();
                window.location.reload();
              }}
              className="hover:bg-[#0077cc] p-1 rounded"
            >
              <RotateCw className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-hidden">
          <ChatFrame 
            messages={messages} 
            setMessages={setMessages} 
            onUploadClick={() => setIsUploadModalOpen(true)}
          />
        </div>
      </div>

      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUpload={handleChatUpload}
      />
      <Toaster />
    </div>
  );
};

export default ChatApp; 