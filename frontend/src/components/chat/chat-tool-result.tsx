"use client";

import { useState } from "react";
import { ChevronRight, Search, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ToolCall } from "@/hooks";

interface ChatToolResultProps {
  tool: ToolCall;
  className?: string;
}

const toolIcons: Record<string, typeof Wrench> = {
  rag: Search,
};

export function ChatToolResult({ tool, className }: ChatToolResultProps) {
  const [isOpen, setIsOpen] = useState(false);
  const Icon = toolIcons[tool.name] || Wrench;

  if (!tool.output) return null;

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
          <Icon className="h-3 w-3" />
          <span>View {tool.name} result</span>
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ScrollArea className="mt-2 max-h-48">
          <div className="rounded-md border bg-muted/30 p-3 text-xs font-mono whitespace-pre-wrap">
            {tool.output}
          </div>
        </ScrollArea>
      </CollapsibleContent>
    </Collapsible>
  );
}
