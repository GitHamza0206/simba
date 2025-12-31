"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CollectionSelector } from "@/components/documents/collection-selector";
import { DocumentUploadZone } from "@/components/documents/document-upload-zone";
import { DocumentsTable } from "@/components/documents/documents-table";
import type { Collection } from "@/types/api";

export default function DocumentsPage() {
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
          <p className="text-muted-foreground">
            Manage your knowledge base documents.
          </p>
        </div>
      </div>

      {/* Collection Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Collection</CardTitle>
          <CardDescription>
            Select or create a collection to organize your documents.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-w-md">
            <CollectionSelector
              selectedId={selectedCollection?.id ?? null}
              onSelect={setSelectedCollection}
            />
          </div>
          {selectedCollection && (
            <p className="mt-2 text-sm text-muted-foreground">
              {selectedCollection.description || `${selectedCollection.document_count} documents`}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Upload Zone */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Upload files to add them to your knowledge base.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DocumentUploadZone
            collectionId={selectedCollection?.id ?? null}
          />
        </CardContent>
      </Card>

      {/* Documents Table */}
      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
          <CardDescription>
            All documents in the selected collection.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DocumentsTable collectionId={selectedCollection?.id ?? null} />
        </CardContent>
      </Card>
    </div>
  );
}
