import React, { useState, useEffect, useRef } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { SimbaDoc } from '@/types/document';
import DocumentList from './DocumentList';
import { Button } from "@/components/ui/button";
import { Plus, Folder, Pencil } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from "@/components/ui/dialog";

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
  const [activeTab, setActiveTab] = useState<string>("all");
  const [editingCollectionId, setEditingCollectionId] = useState<string | null>(null);
  const [editedCollectionName, setEditedCollectionName] = useState<string>("");
  const [showNewCollectionDialog, setShowNewCollectionDialog] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState("");
  const { toast } = useToast();

  const transformedCollections: CustomCollection[] = collections.map(collection => ({
    ...collection,
    displayName: collection.name === 'Default Collection' ? '默认合集' : collection.name
  }));

  const allDocumentsCollection: CustomCollection = {
    id: 'all',
    name: 'All Documents',
    displayName: '所有文档',
    documents: collections.reduce((acc, curr) => acc.concat(curr.documents), [] as SimbaDoc[])
  };

  const displayCollections = [allDocumentsCollection, ...transformedCollections];

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
  };

  const handleNewCollection = () => {
    const newCount = displayCollections.length;
    setActiveTab(`custom-collection-${Date.now()}`);
    setNewCollectionName(`Collection ${newCount}`);
    setShowNewCollectionDialog(true);
  };

  const startEditing = (collection: CustomCollection, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingCollectionId(collection.id);
    setEditedCollectionName(collection.displayName);
  };

  const handleEditKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      finishEditing();
    } else if (e.key === 'Escape') {
      setEditingCollectionId(null);
    }
  };

  const finishEditing = () => {
    if (editingCollectionId && editedCollectionName.trim() !== "") {
      const collectionToUpdate = collections.find(c => c.id === editingCollectionId);
      if (collectionToUpdate) {
        const updatedCollection = { ...collectionToUpdate, name: editedCollectionName };
        setCollections(prevCollections => 
          prevCollections.map(c => c.id === editingCollectionId ? updatedCollection : c)
        );
        toast({ title: "合集已更新", description: `合集 "${editedCollectionName}" 已成功更新。` });
      }
      setEditingCollectionId(null);
      setEditedCollectionName("");
    }
  };

  if (displayCollections.length === 0) {
    return <div className="p-8 text-center text-muted-foreground">加载合集...</div>;
  }
  
  const activeCollection = displayCollections.find(c => c.id === activeTab) || displayCollections[0];

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col w-full h-full">
      <div className="flex items-center bg-muted/20">
        <div className="h-12 flex-1 p-0 flex bg-transparent rounded-none justify-start">
          <TabsList className="flex-1">
            {displayCollections.map((collection) => (
              <TabsTrigger
                key={collection.id}
                value={collection.id}
                className="relative group data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm"
              >
                {editingCollectionId === collection.id ? (
                  <Input
                    type="text"
                    value={editedCollectionName}
                    onChange={(e) => setEditedCollectionName(e.target.value)}
                    onKeyDown={handleEditKeyDown}
                    onBlur={finishEditing}
                    autoFocus
                    className="h-7 px-2 py-1 text-sm bg-white border-primary ring-primary"
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  collection.displayName
                )}
                {collection.id !== 'all' && editingCollectionId !== collection.id && (
                  <Button 
                    variant="ghost"
                    size="icon"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 opacity-0 group-hover:opacity-100"
                    onClick={(e) => startEditing(collection, e)}
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>
                )}
              </TabsTrigger>
            ))}
            <Button variant="outline" size="sm" className="ml-2 h-9" onClick={() => setShowNewCollectionDialog(true)}>
              <Plus className="h-4 w-4 mr-1" /> 新建合集
            </Button>
          </TabsList>
        </div>
      </div>
      {displayCollections.map((collection) => (
        <TabsContent key={collection.id} value={collection.id} className="flex-1 py-6">
          <DocumentList
            documents={collection.documents}
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
        </TabsContent>
      ))}
      <Dialog open={showNewCollectionDialog} onOpenChange={setShowNewCollectionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建新合集</DialogTitle>
            <DialogDescription>
              为您的文档输入一个名称。
            </DialogDescription>
          </DialogHeader>
          <Input 
            placeholder="合集名称"
            value={newCollectionName}
            onChange={(e) => setNewCollectionName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleNewCollection()}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewCollectionDialog(false)}>取消</Button>
            <Button onClick={handleNewCollection} disabled={!newCollectionName.trim()}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Tabs>
  );
};

export default CollectionTabs; 