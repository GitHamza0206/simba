"use client";

import { useState } from "react";
import { Plus, ChevronDown, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCollections, useCreateCollection } from "@/hooks";
import type { Collection } from "@/types/api";

interface CollectionSelectorProps {
  selectedId: string | null;
  onSelect: (collection: Collection) => void;
}

export function CollectionSelector({ selectedId, onSelect }: CollectionSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");

  const { data, isLoading } = useCollections();
  const createMutation = useCreateCollection();

  const collections = data?.items ?? [];
  const selected = collections.find((c) => c.id === selectedId);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    try {
      const newCollection = await createMutation.mutateAsync({
        name: newName.trim(),
        description: newDescription.trim() || undefined,
      });
      onSelect(newCollection);
      setNewName("");
      setNewDescription("");
      setShowCreate(false);
      setIsOpen(false);
    } catch (error) {
      console.error("Failed to create collection:", error);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-10 w-full items-center justify-between rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <span className="flex items-center gap-2">
          <FolderOpen className="h-4 w-4 text-muted-foreground" />
          {isLoading ? (
            "Loading..."
          ) : selected ? (
            selected.name
          ) : (
            <span className="text-muted-foreground">Select a collection</span>
          )}
        </span>
        <ChevronDown className="h-4 w-4 text-muted-foreground" />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-background shadow-lg">
          <div className="max-h-60 overflow-auto p-1">
            {collections.length === 0 && !showCreate ? (
              <div className="px-3 py-8 text-center text-sm text-muted-foreground">
                No collections yet. Create one to get started.
              </div>
            ) : (
              collections.map((collection) => (
                <button
                  key={collection.id}
                  type="button"
                  onClick={() => {
                    onSelect(collection);
                    setIsOpen(false);
                  }}
                  className={`flex w-full items-center justify-between rounded px-3 py-2 text-sm hover:bg-muted ${
                    collection.id === selectedId ? "bg-muted" : ""
                  }`}
                >
                  <span>{collection.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {collection.document_count} docs
                  </span>
                </button>
              ))
            )}
          </div>

          <div className="border-t p-2">
            {showCreate ? (
              <form onSubmit={handleCreate} className="space-y-2">
                <input
                  type="text"
                  placeholder="Collection name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  autoFocus
                />
                <input
                  type="text"
                  placeholder="Description (optional)"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    size="sm"
                    disabled={!newName.trim() || createMutation.isPending}
                  >
                    {createMutation.isPending ? "Creating..." : "Create"}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => setShowCreate(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            ) : (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="w-full justify-start"
                onClick={() => setShowCreate(true)}
              >
                <Plus className="mr-2 h-4 w-4" />
                New Collection
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
