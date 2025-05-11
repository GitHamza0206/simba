import React, { useState, useEffect, useRef } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { SimbaDoc } from '@/types/document';
import DocumentList from './DocumentList';
import { Button } from "@/components/ui/button";
import { Plus, Folder, Pencil } from "lucide-react";
import { Input } from "@/components/ui/input";

interface CollectionTabsProps {
  collections: {
    id: string;
    name: string;
    documents: SimbaDoc[];
  }[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  onSearch: (query: string) => void;
  onUpload: (files: FileList) => void;
  onPreview: (document: SimbaDoc) => void;
  fetchDocuments: () => void;
  onDocumentUpdate: (document: SimbaDoc) => void;
  onParse: (document: SimbaDoc) => void;
  onDisable: (document: SimbaDoc) => void;
  onEnable: (document: SimbaDoc) => void;
}

interface CustomCollection {
  id: string;
  name: string;
  displayName: string;
  documents: SimbaDoc[];
}

const CollectionTabs: React.FC<CollectionTabsProps> = ({
  collections,
  isLoading,
  onDelete,
  onSearch,
  onUpload,
  onPreview,
  fetchDocuments,
  onDocumentUpdate,
  onParse,
  onDisable,
  onEnable,
}) => {
  // Initial collections setup with a dummy collection if empty
  const [customCollections, setCustomCollections] = useState<CustomCollection[]>([]);
  const [activeTab, setActiveTab] = useState<string>('default');
  const [collectionCount, setCollectionCount] = useState<number>(0);
  const [editingTabId, setEditingTabId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState<string>('');
  const editInputRef = useRef<HTMLInputElement>(null);

  // Initialize collections from props
  useEffect(() => {
    if (collections.length > 0) {
      const mappedCollections = collections.map((collection, index) => ({
        ...collection,
        displayName: collection.name === 'Default Collection' ? `Collection ${index + 1}` : collection.name
      }));
      
      setCustomCollections(mappedCollections);
      setCollectionCount(mappedCollections.length);
      
      if (!mappedCollections.some(c => c.id === activeTab)) {
        setActiveTab(mappedCollections[0]?.id || 'default');
      }
    } else if (customCollections.length === 0) {
      // Create a default collection if none exist
      const defaultCollection = { 
        id: 'default', 
        name: 'Default Collection', 
        displayName: 'Collection 1', 
        documents: [] 
      };
      setCustomCollections([defaultCollection]);
      setActiveTab('default');
      setCollectionCount(1);
    }
  }, [collections]);

  // Focus input when editing starts
  useEffect(() => {
    if (editingTabId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingTabId]);

  const handleNewCollection = () => {
    const newCount = collectionCount + 1;
    setCollectionCount(newCount);
    
    // Create a new collection with a unique ID
    const newCollectionId = `custom-collection-${Date.now()}`;
    const newCollection: CustomCollection = {
      id: newCollectionId,
      name: `Collection ${newCount}`,
      displayName: `Collection ${newCount}`,
      documents: []
    };
    
    // Add the new tab to the list but keep the existing ones
    setCustomCollections(prev => [...prev, newCollection]);
    // Make the new tab active immediately
    setActiveTab(newCollectionId);
  };

  const startEditing = (collection: CustomCollection, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent tab switching when clicking edit
    setEditingTabId(collection.id);
    setEditingName(collection.displayName);
  };

  const handleEditKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      finishEditing();
    } else if (e.key === 'Escape') {
      setEditingTabId(null);
    }
  };

  const finishEditing = () => {
    if (editingTabId && editingName.trim()) {
      setCustomCollections(prev =>
        prev.map(collection =>
          collection.id === editingTabId
            ? { ...collection, displayName: editingName.trim(), name: editingName.trim() }
            : collection
        )
      );
    }
    setEditingTabId(null);
  };

  // Return early if no collections
  if (customCollections.length === 0) {
    return <div className="p-8 text-center text-muted-foreground">Loading collections...</div>;
  }
  
  // Get active collection
  const activeCollection = customCollections.find(c => c.id === activeTab) || customCollections[0];

  return (
    <div className="flex flex-col w-full h-full">
      <div className="flex items-center bg-muted/20">
        <div className="h-12 flex-1 p-0 flex bg-transparent rounded-none justify-start">
          {customCollections.map((collection) => (
            <button
              key={collection.id}
              className={`relative px-6 h-12 rounded-t-lg rounded-b-none border-b-2 hover:bg-background/60 
                group flex items-center gap-2 
                ${activeTab === collection.id 
                  ? 'border-primary bg-background shadow-none' 
                  : 'border-transparent'}`}
              onClick={() => {
                if (editingTabId) finishEditing();
                setActiveTab(collection.id);
              }}
            >
              <Folder className="h-4 w-4 text-muted-foreground shrink-0" />
              
              {editingTabId === collection.id ? (
                <Input
                  ref={editInputRef}
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  onKeyDown={handleEditKeyDown}
                  onBlur={finishEditing}
                  className="h-7 px-2 py-0 w-[140px] bg-transparent"
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <>
                  <span className="truncate max-w-[140px]">{collection.displayName}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => startEditing(collection, e)}
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>
                </>
              )}
            </button>
          ))}
          <Button 
            size="sm" 
            variant="ghost" 
            className="h-12 px-3 text-muted-foreground rounded-none hover:bg-background/60"
            onClick={handleNewCollection}
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      <div className="flex-1 py-6">
        {/* Render only the active collection's documents */}
        <DocumentList
          documents={activeCollection.documents}
          isLoading={isLoading}
          onDelete={onDelete}
          onSearch={onSearch}
          onUpload={onUpload}
          onPreview={onPreview}
          fetchDocuments={fetchDocuments}
          onDocumentUpdate={onDocumentUpdate}
          onParse={onParse}
          onDisable={onDisable}
          onEnable={onEnable}
        />
      </div>
    </div>
  );
};

export default CollectionTabs; 