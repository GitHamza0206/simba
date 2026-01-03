"use client";

import { useState } from "react";
import { ChevronRight, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ToolCall } from "@/hooks";

interface ChatContextProps {
  tool: ToolCall;
  className?: string;
}

interface ParsedChunk {
  source: string;
  content: string;
}

function parseRagOutput(output: string): ParsedChunk[] {
  const chunks: ParsedChunk[] = [];
  const parts = output.split("\n\n---\n\n");

  for (const part of parts) {
    const match = part.match(/^\[Source \d+: (.+?)\]\n([\s\S]+)$/);
    if (match) {
      chunks.push({
        source: match[1],
        content: match[2].trim(),
      });
    }
  }

  return chunks;
}

export function ChatContext({ tool, className }: ChatContextProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set());

  if (tool.name !== "rag" || !tool.output) return null;

  const chunks = parseRagOutput(tool.output);
  if (chunks.length === 0) return null;

  const toggleChunk = (idx: number) => {
    setExpandedChunks((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className={cn("mt-2", className)}
    >
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronRight
            className={cn(
              "h-3 w-3 transition-transform duration-200",
              isOpen && "rotate-90"
            )}
          />
          <FileText className="h-3 w-3" />
          <span>
            View retrieved context ({chunks.length} chunk
            {chunks.length !== 1 ? "s" : ""})
          </span>
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ScrollArea className="mt-2 max-h-64">
          <div className="space-y-2">
            {chunks.map((chunk, idx) => (
              <div
                key={idx}
                className="rounded-md border bg-muted/30 overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => toggleChunk(idx)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:bg-muted/50 transition-colors text-left"
                >
                  <ChevronRight
                    className={cn(
                      "h-3 w-3 shrink-0 transition-transform duration-200",
                      expandedChunks.has(idx) && "rotate-90"
                    )}
                  />
                  <FileText className="h-3 w-3 shrink-0 text-muted-foreground" />
                  <span className="font-medium truncate">{chunk.source}</span>
                </button>
                {expandedChunks.has(idx) && (
                  <div className="px-3 pb-3 pt-1 text-xs text-muted-foreground whitespace-pre-wrap border-t">
                    {chunk.content}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CollapsibleContent>
    </Collapsible>
  );
}
