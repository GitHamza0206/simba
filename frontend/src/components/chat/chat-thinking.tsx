"use client";

import { useState } from "react";
import { Brain, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface ChatThinkingProps {
  thinking: string;
  className?: string;
}

export function ChatThinking({ thinking, className }: ChatThinkingProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!thinking) return null;

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
          <Brain className="h-3 w-3" />
          <span>View reasoning</span>
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent className="data-[state=open]:animate-collapsible-down data-[state=closed]:animate-collapsible-up">
        <div className="mt-2 rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
          <p className="whitespace-pre-wrap leading-relaxed">{thinking}</p>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
