"use client";

import { useState } from "react";
import {
  FileText,
  Trash2,
  RefreshCw,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDocuments, useDeleteDocument, useReprocessDocument } from "@/hooks";
import { ChunksViewer } from "./chunks-viewer";
import type { Document, DocumentStatus } from "@/types/api";
import { API_URL } from "@/lib/constants";

interface DocumentsTableProps {
  collectionId: string | null;
}

function StatusBadge({ status }: { status: DocumentStatus }) {
  const config = {
    pending: {
      icon: Clock,
      className: "text-yellow-600 bg-yellow-100",
      label: "Pending",
    },
    processing: {
      icon: Loader2,
      className: "text-blue-600 bg-blue-100",
      label: "Processing",
      spin: true,
    },
    ready: {
      icon: CheckCircle,
      className: "text-green-600 bg-green-100",
      label: "Ready",
    },
    failed: {
      icon: AlertCircle,
      className: "text-red-600 bg-red-100",
      label: "Failed",
    },
  }[status];

  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${config.className}`}
    >
      <Icon className={`h-3 w-3 ${config.spin ? "animate-spin" : ""}`} />
      {config.label}
    </span>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function DocumentsTable({ collectionId }: DocumentsTableProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [reprocessingId, setReprocessingId] = useState<string | null>(null);
  const [viewingChunks, setViewingChunks] = useState<Document | null>(null);

  const { data, isLoading } = useDocuments({ collectionId: collectionId ?? undefined });
  const deleteMutation = useDeleteDocument();
  const reprocessMutation = useReprocessDocument();

  const documents = data?.items ?? [];
  const hasProcessing = documents.some(
    (d) => d.status === "pending" || d.status === "processing"
  );

  // Auto-refresh while documents are processing
  const refetchInterval = hasProcessing ? 3000 : false;

  const handleDelete = async (doc: Document) => {
    if (!confirm(`Delete "${doc.name}"? This cannot be undone.`)) return;

    setDeletingId(doc.id);
    try {
      await deleteMutation.mutateAsync(doc.id);
    } finally {
      setDeletingId(null);
    }
  };

  const handleReprocess = async (doc: Document) => {
    setReprocessingId(doc.id);
    try {
      await reprocessMutation.mutateAsync(doc.id);
    } finally {
      setReprocessingId(null);
    }
  };

  const handleDownload = (doc: Document) => {
    window.open(`${API_URL}/api/v1/documents/${doc.id}/download`, "_blank");
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!collectionId) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        Select a collection to view documents
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <FileText className="h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-sm text-muted-foreground">
          No documents in this collection yet
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {hasProcessing && (
        <div className="flex items-center justify-end gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Processing documents...
        </div>
      )}

      <div className="rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-3 text-left font-medium">Name</th>
              <th className="p-3 text-left font-medium">Status</th>
              <th className="p-3 text-left font-medium">Chunks</th>
              <th className="p-3 text-left font-medium">Size</th>
              <th className="p-3 text-left font-medium">Uploaded</th>
              <th className="p-3 text-left font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id} className="border-b last:border-0">
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{doc.name}</span>
                  </div>
                  {doc.error_message && (
                    <p className="mt-1 text-xs text-red-600">{doc.error_message}</p>
                  )}
                </td>
                <td className="p-3">
                  <StatusBadge status={doc.status} />
                </td>
                <td className="p-3 text-muted-foreground">{doc.chunk_count}</td>
                <td className="p-3 text-muted-foreground">
                  {formatBytes(doc.size_bytes)}
                </td>
                <td className="p-3 text-muted-foreground">
                  {formatDate(doc.created_at)}
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-1">
                    {doc.status === "ready" && doc.chunk_count > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setViewingChunks(doc)}
                        title="View Chunks"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownload(doc)}
                      title="Download"
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    {(doc.status === "failed" || doc.status === "ready") && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleReprocess(doc)}
                        disabled={reprocessingId === doc.id}
                        title="Reprocess"
                      >
                        <RefreshCw
                          className={`h-4 w-4 ${
                            reprocessingId === doc.id ? "animate-spin" : ""
                          }`}
                        />
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(doc)}
                      disabled={deletingId === doc.id}
                      title="Delete"
                      className="text-red-600 hover:text-red-700"
                    >
                      {deletingId === doc.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-right text-sm text-muted-foreground">
        {data?.total ?? 0} document(s)
      </div>

      {/* Chunks Viewer Modal */}
      {viewingChunks && (
        <ChunksViewer
          documentId={viewingChunks.id}
          documentName={viewingChunks.name}
          onClose={() => setViewingChunks(null)}
        />
      )}
    </div>
  );
}
