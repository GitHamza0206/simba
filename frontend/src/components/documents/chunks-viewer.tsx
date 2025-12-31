"use client";

import { X, FileText, Loader2, Hash, Copy, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useDocumentChunks } from "@/hooks/useDocuments";

interface ChunksViewerProps {
  documentId: string;
  documentName: string;
  onClose: () => void;
}

export function ChunksViewer({ documentId, documentName, onClose }: ChunksViewerProps) {
  const { data, isLoading, error } = useDocumentChunks(documentId);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = async (text: string, chunkId: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(chunkId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative z-10 flex max-h-[85vh] w-full max-w-3xl flex-col rounded-lg border bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5 text-muted-foreground" />
            <div>
              <h2 className="font-semibold">Document Chunks</h2>
              <p className="text-sm text-muted-foreground">{documentName}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
              {error instanceof Error ? error.message : "Failed to load chunks"}
            </div>
          ) : data?.chunks.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              No chunks found for this document.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">
                {data?.chunk_count} chunk(s) total
              </div>

              {data?.chunks.map((chunk, index) => (
                <div
                  key={chunk.id}
                  className="rounded-lg border bg-muted/30 p-4"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Hash className="h-3 w-3" />
                      <span>Chunk {chunk.position + 1}</span>
                      <span className="text-xs">({chunk.text.length} chars)</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopy(chunk.text, chunk.id)}
                      className="h-7 px-2"
                    >
                      {copiedId === chunk.id ? (
                        <Check className="h-3 w-3 text-green-600" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </Button>
                  </div>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">
                    {chunk.text}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4">
          <Button variant="outline" onClick={onClose} className="w-full">
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
