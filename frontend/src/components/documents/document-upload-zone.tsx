"use client";

import { useState, useCallback } from "react";
import { Upload, X, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUploadDocument } from "@/hooks";

interface DocumentUploadZoneProps {
  collectionId: string | null;
  onUploadComplete?: () => void;
}

interface PendingFile {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  error?: string;
}

export function DocumentUploadZone({ collectionId, onUploadComplete }: DocumentUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([]);

  const uploadMutation = useUploadDocument();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    addFiles(files);
    e.target.value = "";
  };

  const addFiles = (files: File[]) => {
    const newPending = files.map((file) => ({
      file,
      status: "pending" as const,
    }));
    setPendingFiles((prev) => [...prev, ...newPending]);
  };

  const removeFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadAll = async () => {
    if (!collectionId) return;

    for (let i = 0; i < pendingFiles.length; i++) {
      const pending = pendingFiles[i];
      if (pending.status !== "pending") continue;

      setPendingFiles((prev) =>
        prev.map((p, idx) => (idx === i ? { ...p, status: "uploading" } : p))
      );

      try {
        await uploadMutation.mutateAsync({
          file: pending.file,
          collectionId,
        });
        setPendingFiles((prev) =>
          prev.map((p, idx) => (idx === i ? { ...p, status: "done" } : p))
        );
      } catch (error) {
        setPendingFiles((prev) =>
          prev.map((p, idx) =>
            idx === i
              ? { ...p, status: "error", error: (error as Error).message }
              : p
          )
        );
      }
    }

    onUploadComplete?.();
  };

  const pendingCount = pendingFiles.filter((f) => f.status === "pending").length;
  const hasFiles = pendingFiles.length > 0;

  return (
    <div className="space-y-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        } ${!collectionId ? "opacity-50" : ""}`}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <Upload className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="mt-4 text-sm font-medium">
          {collectionId
            ? "Drag and drop files here, or click to browse"
            : "Select a collection first"}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Supports PDF, DOCX, TXT, and MD files
        </p>
        <label className="mt-4">
          <input
            type="file"
            multiple
            onChange={handleFileSelect}
            disabled={!collectionId}
            className="hidden"
            accept=".pdf,.docx,.doc,.txt,.md"
          />
          <Button
            type="button"
            variant="outline"
            disabled={!collectionId}
            asChild
          >
            <span className="cursor-pointer">Browse Files</span>
          </Button>
        </label>
      </div>

      {hasFiles && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              {pendingCount} file(s) ready to upload
            </span>
            <Button
              size="sm"
              onClick={uploadAll}
              disabled={!collectionId || pendingCount === 0}
            >
              Upload All
            </Button>
          </div>

          <div className="space-y-1">
            {pendingFiles.map((pending, index) => (
              <div
                key={index}
                className="flex items-center justify-between rounded-md border bg-muted/50 px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{pending.file.name}</span>
                  <span className="text-xs text-muted-foreground">
                    ({(pending.file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {pending.status === "uploading" && (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  )}
                  {pending.status === "done" && (
                    <span className="text-xs text-green-600">Uploaded</span>
                  )}
                  {pending.status === "error" && (
                    <span className="text-xs text-red-600">{pending.error}</span>
                  )}
                  {pending.status === "pending" && (
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
