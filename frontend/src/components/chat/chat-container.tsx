"use client";

import { useRef, useEffect, useState, type ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatContainerProps {
  children: ReactNode;
  className?: string;
  autoScroll?: boolean;
}

export function ChatContainer({
  children,
  className,
  autoScroll = true,
}: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [isAtBottom, setIsAtBottom] = useState(true);

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  const handleScroll = () => {
    if (!scrollRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    const atBottom = distanceFromBottom < 100;

    setIsAtBottom(atBottom);
    setShowScrollButton(!atBottom);
  };

  useEffect(() => {
    if (autoScroll && isAtBottom) {
      scrollToBottom();
    }
  }, [children, autoScroll, isAtBottom]);

  return (
    <div className={cn("relative flex-1 overflow-hidden", className)}>
      <ScrollArea
        ref={scrollRef}
        className="h-full"
        onScrollCapture={handleScroll}
      >
        <div className="flex flex-col gap-1 p-4">{children}</div>
      </ScrollArea>

      {showScrollButton && (
        <Button
          variant="secondary"
          size="icon"
          className="absolute bottom-4 right-4 h-8 w-8 rounded-full shadow-md"
          onClick={scrollToBottom}
        >
          <ChevronDown className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
