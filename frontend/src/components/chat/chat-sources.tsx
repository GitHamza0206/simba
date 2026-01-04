"use client";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface Source {
  document_name: string;
  content: string;
  score?: number;
}

interface ChatSourcesProps {
  sources: Source[];
  className?: string;
}

export function ChatSources({ sources, className }: ChatSourcesProps) {
  if (sources.length === 0) return null;

  return (
    <TooltipProvider>
      <div className={cn("flex flex-wrap items-center gap-1 mt-2", className)}>
        <span className="text-xs text-muted-foreground mr-1">Sources:</span>
        {sources.map((source, idx) => (
          <Tooltip key={idx} delayDuration={200}>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="inline-flex items-center justify-center h-5 min-w-5 px-1.5 text-[10px] font-medium rounded bg-muted hover:bg-muted/80 text-muted-foreground transition-colors"
              >
                {idx + 1}
              </button>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs">
              <div className="space-y-1">
                <p className="font-medium text-xs">{source.document_name}</p>
                {source.score !== undefined && (
                  <p className="text-[10px] text-muted-foreground">
                    Relevance: {Math.round(source.score * 100)}%
                  </p>
                )}
                {source.content && (
                  <p className="text-[10px] text-muted-foreground line-clamp-3">
                    {source.content}
                  </p>
                )}
              </div>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
}
