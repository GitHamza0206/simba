import React, { useState, useEffect } from 'react';
import { Card } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Toaster } from "@/components/ui/toaster";
import { Progress } from "@/components/ui/progress";
import DocumentManagementHeader from '@/components/DocumentManagement/DocumentManagementHeader';
import DocumentList from '@/components/DocumentManagement/DocumentList';
import { DocumentType, DocumentStatsType } from '@/types/document';
import { ingestionApi } from '@/lib/ingestion_api';
import PreviewModal from '@/components/DocumentManagement/PreviewModal';

import { folderApi } from '@/lib/folder_api';

interface DocumentManagementHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  stats: DocumentStatsType;
}

// Utility function to handle browser-side caching
const useLocalCache = (key: string, ttl = 60000) => { // 60 seconds TTL by default
  const getCache = () => {
    try {
      const cacheItem = localStorage.getItem(key);
      if (!cacheItem) return null;
      
      const { value, expiry } = JSON.parse(cacheItem);
      if (Date.now() > expiry) {
        localStorage.removeItem(key);
        return null;
      }
      return value;
    } catch (error) {
      console.error('Cache retrieval error:', error);
      return null;
    }
  };

  const setCache = (value: any) => {
    try {
      const cacheItem = {
        value,
        expiry: Date.now() + ttl,
      };
      localStorage.setItem(key, JSON.stringify(cacheItem));
    } catch (error) {
      console.error('Cache storage error:', error);
    }
  };

  const clearCache = () => {
    localStorage.removeItem(key);
  };

  return { getCache, setCache, clearCache };
};

const DocumentManagementApp: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();
  const [selectedDocument, setSelectedDocument] = useState<DocumentType | null>(null);
  const [loadingStatus, setLoadingStatus] = useState<string>("Loading...");
  const { getCache, setCache, clearCache } = useLocalCache('documentCache', 300000); // 5-minute cache

  // New handlers for multi-select actions
  const handleParse = async (doc: DocumentType) => {
    console.log("Parsing document:", doc.id);
    // TODO: implement actual parse logic
    toast({ title: "Parsing", description: `Parsing document ${doc.id}` });
  };

  const handleDisable = async (doc: DocumentType) => {
    console.log("Disabling document:", doc.id);
    // TODO: implement actual disable logic
    toast({ title: "Disable", description: `Disabling document ${doc.id}` });
  };

  const handleEnable = async (doc: DocumentType) => {
    console.log("Enabling document:", doc.id);
    // TODO: implement actual enable logic
    toast({ title: "Enable", description: `Enabling document ${doc.id}` });
  };

  const stats: DocumentStatsType = {
    lastQueried: "2 hours ago",
    totalQueries: 145,
    itemsIndexed: documents.filter(doc => !doc.is_folder).length,
    createdAt: "Apr 12, 2024"
  };

  const fetchDocuments = async () => {
    // Check cache first
    const cachedDocs = getCache();
    if (cachedDocs) {
      console.log('Using cached documents');
      setDocuments(cachedDocs);
      return;
    }
    
    setIsLoading(true);
    try {
      const docs = await ingestionApi.getDocuments();
      setDocuments(docs);
      
      // Cache the documents
      setCache(docs);
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
      setDocuments(docs => docs.filter(doc => doc.id !== id));
      // Update cache after delete
      clearCache();
      toast({
        title: "Success",
        description: "Document successfully deleted",
      });
    } catch (error: any) {
      if (error.message !== 'Delete cancelled by user') {
        toast({
          variant: "destructive",
          title: "Error",
          description: error.message || "Failed to delete document",
        });
      }
    }
  };

  const handleSearch = (query: string) => {
    console.log('Searching:', query);
  };

  const handlePreview = (document: DocumentType) => {
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
      // Clear cache to force fetching fresh data after upload
      clearCache();
      await fetchDocuments();
      toast({
        title: "Success",
        description: `${uploadedDocs.length} ${uploadedDocs.length === 1 ? 'file' : 'files'} uploaded successfully`,
      });
    } catch (error: any) {
      console.error('Upload error:', error);
      toast({
        variant: "destructive",
        title: "Upload Failed",
        description: error.message || "Failed to upload files. Please try again.",
      });
    } finally {
      setIsLoading(false);
      setProgress(0);
      setLoadingStatus("");
    }
  };

  const handleDocumentUpdate = (updatedDoc: DocumentType) => {
    setDocuments(prev => prev.map(doc => doc.id === updatedDoc.id ? updatedDoc : doc));
    // Update cache after document update
    clearCache();
  };

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 p-6">
        {isLoading && (
          <div className="fixed inset-0 bg-background/50 backdrop-blur-sm flex flex-col gap-4 items-center justify-center z-50">
            <Progress value={progress} className="w-[60%] max-w-md" />
            <p className="text-sm text-muted-foreground">{loadingStatus} {progress}%</p>
          </div>
        )}
        <Card className="bg-white shadow-xl rounded-xl h-full flex flex-col">
          <DocumentManagementHeader stats={stats} />
          <DocumentList
            documents={documents}
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
        </Card>
      </div>
      <PreviewModal 
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        document={selectedDocument}
        onUpdate={(updatedDoc) => {
          setDocuments(prev => prev.map(doc => doc.id === updatedDoc.id ? updatedDoc : doc));
          setSelectedDocument(updatedDoc);
          // Update cache after document update in modal
          clearCache();
        }}
      />
      <Toaster />
    </div>
  );
};

export default DocumentManagementApp; 