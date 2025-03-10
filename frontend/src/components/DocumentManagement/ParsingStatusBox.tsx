import React, { useEffect, useState } from 'react';
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import { Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { parsingApi } from '@/lib/parsing_api';
import { cn } from '@/lib/utils';

interface ParsingStatusBoxProps {
  taskId: string | null;
  onComplete?: (status: string) => void;
  onCancel?: () => void;
}

export const ParsingStatusBox: React.FC<ParsingStatusBoxProps> = ({ taskId, onComplete, onCancel }) => {
  const [status, setStatus] = useState<string>('pending');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const pollStatus = async () => {
      try {
        const result = await parsingApi.getParseStatus(taskId);
        setStatus(result.status);
        
        if (result.status === 'SUCCESS') {
          setProgress(100);
          if (onComplete) onComplete('PARSED');
        } else if (result.status === 'FAILURE') {
          setError(result.result?.error || 'Parsing failed');
          if (onComplete) onComplete('FAILED');
        } else if (result.progress !== undefined) {
          setProgress(result.progress);
        }
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to get parsing status');
        setStatus('error');
        if (onComplete) onComplete('FAILED');
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [taskId, onComplete]);

  if (!taskId) return null;

  return (
    <HoverCard>
      <HoverCardTrigger asChild>
        <div className="flex items-center gap-2 cursor-pointer">
          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
        </div>
      </HoverCardTrigger>
      <HoverCardContent className="w-auto p-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{progress}%</span>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-6 w-6 hover:bg-red-100 hover:text-red-600"
            onClick={onCancel}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}; 