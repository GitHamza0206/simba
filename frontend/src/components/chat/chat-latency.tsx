"use client";

import { Zap, Database, Bot, Hash } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { LatencyBreakdown } from "@/hooks";

interface ChatLatencyProps {
  latency?: {
    retrieval?: LatencyBreakdown;
    response?: LatencyBreakdown;
  };
  className?: string;
}

function formatMs(ms: number | undefined): string {
  if (ms === undefined || ms === null) return "-";
  if (ms < 1) return "<1ms";
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

interface MetricRowProps {
  label: string;
  value: number | undefined;
}

function MetricRow({ label, value }: MetricRowProps) {
  if (value === undefined) return null;

  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono">{formatMs(value)}</span>
    </div>
  );
}

function formatTokenCount(count: number | undefined): string {
  if (count === undefined || count === null) return "-";
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`;
  return count.toString();
}

interface TokenRowProps {
  label: string;
  value: number | undefined;
}

function TokenRow({ label, value }: TokenRowProps) {
  if (value === undefined || value === 0) return null;

  return (
    <div className="flex items-center justify-between py-0.5">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono">{formatTokenCount(value)}</span>
    </div>
  );
}

export function ChatLatency({ latency, className }: ChatLatencyProps) {
  if (!latency) return null;

  const { retrieval, response } = latency;

  // Calculate retrieval total
  const retrievalTotal =
    retrieval &&
    (retrieval.total_ms ??
      (retrieval.embedding_ms ?? 0) +
        (retrieval.search_ms ?? 0) +
        (retrieval.rerank_ms ?? 0));

  // Response total comes from backend
  const responseTotal = response?.total_ms;

  const hasRetrievalData = retrievalTotal !== undefined && retrievalTotal > 0;
  const hasResponseData = responseTotal !== undefined && responseTotal > 0;

  // Check for token data
  const hasTokenData =
    (response?.input_tokens ?? 0) > 0 ||
    (response?.output_tokens ?? 0) > 0 ||
    (response?.reasoning_tokens ?? 0) > 0;

  // Calculate total output tokens (reasoning + non-reasoning)
  const totalOutputTokens =
    (response?.output_tokens ?? 0) + (response?.reasoning_tokens ?? 0);

  if (!hasRetrievalData && !hasResponseData) return null;

  // Grand total = response total (includes everything)
  const grandTotal = responseTotal ?? retrievalTotal ?? 0;

  return (
    <TooltipProvider>
      <Tooltip delayDuration={200}>
        <TooltipTrigger asChild>
          <button
            type="button"
            className={cn(
              "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-muted/80 text-foreground hover:bg-muted transition-colors",
              className
            )}
          >
            <Zap className="h-3 w-3 text-amber-500" />
            <span>{formatMs(grandTotal)}</span>
          </button>
        </TooltipTrigger>
        <TooltipContent side="top" align="start" className="w-56 p-0">
          {/* Header */}
          <div className="px-3 py-2 border-b bg-muted/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold">Latency</span>
              <span className="text-xs font-mono font-bold">
                {formatMs(grandTotal)}
              </span>
            </div>
          </div>

          <div className="p-3 text-xs space-y-3">
            {/* Retrieval Section */}
            {hasRetrievalData && (
              <div>
                <div className="flex items-center gap-1.5 mb-1.5 pb-1 border-b border-dashed">
                  <Database className="h-3 w-3" />
                  <span className="font-medium">Retrieval</span>
                  <span className="ml-auto font-mono font-medium">
                    {formatMs(retrievalTotal)}
                  </span>
                </div>
                <div className="pl-4 space-y-0.5">
                  <MetricRow label="Embedding" value={retrieval!.embedding_ms} />
                  <MetricRow label="Search" value={retrieval!.search_ms} />
                  <MetricRow label="Rerank" value={retrieval!.rerank_ms} />
                </div>
              </div>
            )}

            {/* Response Section */}
            {hasResponseData && (
              <div>
                <div className="flex items-center gap-1.5 mb-1.5 pb-1 border-b border-dashed">
                  <Bot className="h-3 w-3" />
                  <span className="font-medium">Response</span>
                  <span className="ml-auto font-mono font-medium">
                    {formatMs(responseTotal)}
                  </span>
                </div>
                <div className="pl-4 space-y-0.5">
                  <MetricRow label="First token" value={response!.ttft_ms} />
                  <MetricRow label="Generation" value={response!.generation_ms} />
                </div>
              </div>
            )}

            {/* Tokens Section */}
            {hasTokenData && (
              <div>
                <div className="flex items-center gap-1.5 mb-1.5 pb-1 border-b border-dashed">
                  <Hash className="h-3 w-3" />
                  <span className="font-medium">Tokens</span>
                  <span className="ml-auto font-mono font-medium">
                    {formatTokenCount(totalOutputTokens)}
                  </span>
                </div>
                <div className="pl-4 space-y-0.5">
                  <TokenRow label="Input" value={response?.input_tokens} />
                  <TokenRow label="Reasoning" value={response?.reasoning_tokens} />
                  <TokenRow label="Output" value={response?.output_tokens} />
                </div>
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
