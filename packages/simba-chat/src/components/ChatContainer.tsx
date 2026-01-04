import { useRef, useEffect, type ReactNode } from "react";
import { cn } from "../utils/cn";

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
  const isAtBottomRef = useRef(true);

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  const handleScroll = () => {
    if (!scrollRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    isAtBottomRef.current = distanceFromBottom < 100;
  };

  useEffect(() => {
    if (autoScroll && isAtBottomRef.current) {
      scrollToBottom();
    }
  }, [children, autoScroll]);

  return (
    <div
      ref={scrollRef}
      className={cn("simba-chat-container", className)}
      onScroll={handleScroll}
    >
      <div className="simba-chat-messages">{children}</div>
    </div>
  );
}
