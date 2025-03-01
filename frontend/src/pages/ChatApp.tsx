import React, { useState, useEffect } from 'react';
import ChatFrame from '@/components/ChatFrame';
import { MoreVertical, RotateCw, MessageSquare } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Message } from '@/types/chat';
import { config } from '@/config';
import { FileUploadModal } from '@/components/DocumentManagement/FileUploadModal';
import { ingestionApi } from '@/lib/ingestion_api';
import { useToast } from '@/hooks/use-toast';
import { Toaster } from "@/components/ui/toaster";
import { motion } from 'framer-motion';

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
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="p-4 md:p-6 h-full flex flex-col"
    >
      <motion.div 
        className="bg-white shadow-xl flex flex-col h-full rounded-xl overflow-hidden border border-gray-100"
        initial={{ y: 20 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5, type: "spring", stiffness: 100 }}
      >
        <div className="bg-gradient-to-r from-[#005ba1] to-[#0077cc] text-white py-3 px-4 flex items-center justify-between shrink-0 rounded-t-xl">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            <h1 className="text-xl font-semibold">{config.appName}</h1>
            {messages.length > 0 && (
              <div className="ml-2 bg-white/20 text-white text-xs rounded-full px-2 py-0.5">
                {messages.length} message{messages.length !== 1 ? 's' : ''}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <motion.button 
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => {
                handleClearMessages();
                window.location.reload();
              }}
              className="hover:bg-white/20 p-2 rounded-full transition-colors duration-200"
            >
              <RotateCw className="h-5 w-5" />
            </motion.button>
            
            <DropdownMenu>
              <DropdownMenuTrigger className="hover:bg-white/20 p-2 rounded-full transition-colors duration-200">
                <MoreVertical className="h-5 w-5" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={handleClearMessages} className="cursor-pointer">
                  Nouvelle discussion
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleEndDiscussion} className="cursor-pointer text-red-500">
                  Terminer la discussion
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        <div className="flex-1 overflow-hidden relative">
          <ChatFrame 
            messages={messages} 
            setMessages={setMessages} 
            onUploadClick={() => setIsUploadModalOpen(true)}
          />
        </div>
      </motion.div>

      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUpload={handleChatUpload}
      />
      <Toaster />
    </motion.div>
  );
};

export default ChatApp; 