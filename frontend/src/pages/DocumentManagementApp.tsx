import React, { useState, useEffect } from 'react';
import { useToast } from "@/hooks/use-toast";
import { Toaster } from "@/components/ui/toaster";
import { Progress } from "@/components/ui/progress";
import DocumentManagementHeader from '@/components/DocumentManagement/DocumentManagementHeader';
import CollectionTabs from '@/components/DocumentManagement/CollectionTabs';
import { SimbaDoc } from '@/types/document';
import { ingestionApi } from '@/lib/ingestion_api';
import PreviewModal from '@/components/DocumentManagement/PreviewModal';

interface DocumentStats {
  lastQueried: string;
  totalQueries: number;
  itemsIndexed: number;
  createdAt: string;
}

interface Collection {
  id: string;
  name: string;
  documents: SimbaDoc[];
}

const DocumentManagementApp: React.FC = () => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();
  const [selectedDocument, setSelectedDocument] = useState<SimbaDoc | null>(null);
  const [loadingStatus, setLoadingStatus] = useState<string>("Loading...");

  // New handlers for multi-select actions
  const handleParse = async (doc: SimbaDoc) => {
    console.log("Parsing document:", doc.id);
    // TODO: implement actual parse logic
    toast({ title: "Parsing", description: `Parsing document ${doc.id}` });
  };

  const handleDisable = async (doc: SimbaDoc) => {
    console.log("Disabling document:", doc.id);
    // TODO: implement actual disable logic
    toast({ title: "Disable", description: `Disabling document ${doc.id}` });
  };

  const handleEnable = async (doc: SimbaDoc) => {
    console.log("Enabling document:", doc.id);
    // TODO: implement actual enable logic
    toast({ title: "Enable", description: `Enabling document ${doc.id}` });
  };

  const stats: DocumentStats = {
    lastQueried: "2 hours ago",
    totalQueries: 145,
    itemsIndexed: collections.reduce((acc, collection) => acc + collection.documents.filter(doc => !doc.metadata.is_folder).length, 0),
    createdAt: "Apr 12, 2024"
  };

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await ingestionApi.getDocuments();
      // Group documents by collection
      const collectionsMap = new Map<string, Collection>();
      
      docs.forEach(doc => {
        const collectionId = doc.metadata.folder_id || 'default';
        if (!collectionsMap.has(collectionId)) {
          collectionsMap.set(collectionId, {
            id: collectionId,
            name: doc.metadata.folder_path || 'Default Collection',
            documents: []
          });
        }
        collectionsMap.get(collectionId)?.documents.push(doc);
      });

      setCollections(Array.from(collectionsMap.values()));
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast({
        variant: "destructive",
        description: "Failed to fetch documents"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch documents when component mounts
  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await ingestionApi.deleteDocument(id);
      setCollections(prev => prev.map(collection => ({
        ...collection,
        documents: collection.documents.filter(doc => doc.id !== id)
      })));
      toast({
        title: "Success",
        description: "Document successfully deleted",
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      if (errorMessage !== 'Delete cancelled by user') {
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage || "Failed to delete document",
        });
      }
    }
  };

  const handleSearch = (query: string) => {
    console.log('Searching:', query);
  };

  const handlePreview = (document: SimbaDoc) => {
    setSelectedDocument(document);
  };

  const handleUpload = async (files: FileList) => {
    if (files.length === 0) return;

    setIsLoading(true);
    setProgress(0);
    setLoadingStatus("Preparing files...");

    try {
      const fileArray = Array.from(files);
      setLoadingStatus("Uploading files...");
      const uploadedDocs = await ingestionApi.uploadDocuments(fileArray);
      setProgress(50);
      setLoadingStatus("Processing documents...");
      await new Promise(resolve => setTimeout(resolve, 1000));
      await fetchDocuments();
      toast({
        title: "Success",
        description: `${uploadedDocs.length} ${uploadedDocs.length === 1 ? 'file' : 'files'} uploaded successfully`,
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Upload error:', error);
      toast({
        variant: "destructive",
        title: "Upload Failed",
        description: errorMessage || "Failed to upload files. Please try again.",
      });
    } finally {
      setIsLoading(false);
      setProgress(0);
      setLoadingStatus("");
    }
  };

  const handleDocumentUpdate = (updatedDoc: SimbaDoc) => {
    setCollections(prev => prev.map(collection => ({
      ...collection,
      documents: collection.documents.map(doc => 
        doc.id === updatedDoc.id ? updatedDoc : doc
      )
    })));
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {isLoading && (
        <div className="fixed inset-0 bg-background/50 backdrop-blur-sm flex flex-col gap-4 items-center justify-center z-50">
          <Progress value={progress} className="w-[60%] max-w-md" />
          <p className="text-sm text-muted-foreground">{loadingStatus} {progress}%</p>
        </div>
      )}
      
      <div className="flex-none p-6 pb-0 bg-background border-b">
        <DocumentManagementHeader stats={stats} />
      </div>

      <div className="flex-1 px-6">
        <CollectionTabs
          collections={collections}
          isLoading={isLoading}
          onDelete={handleDelete}
          onSearch={handleSearch}
          onUpload={handleUpload}
          onPreview={handlePreview}
          fetchDocuments={fetchDocuments}
          onDocumentUpdate={handleDocumentUpdate}
          onParse={handleParse}
          onDisable={handleDisable}
          onEnable={handleEnable}
        />
      </div>

      <PreviewModal 
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        document={selectedDocument}
        onUpdate={(updatedDoc) => {
          handleDocumentUpdate(updatedDoc);
          setSelectedDocument(updatedDoc);
        }}
      />
      <Toaster />
    </div>
  );
};

export default DocumentManagementApp; 