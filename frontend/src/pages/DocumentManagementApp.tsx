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

const DocumentManagementApp: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();
  const [previewContent, setPreviewContent] = useState<string>("");
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentType | null>(null);
  const [loadingStatus, setLoadingStatus] = useState<string>("Loading...");

  

  const stats: DocumentStatsType = {
    lastQueried: "2 hours ago",
    totalQueries: 145,
    itemsIndexed: documents.filter(doc => !doc.is_folder).length,
    createdAt: "Apr 12, 2024"
  };

  

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await ingestionApi.getDocuments();
      setDocuments(docs);
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
  }, []); // Empty dependency array means this runs once on mount

  const handleDelete = async (id: string) => {
    try {
      await ingestionApi.deleteDocument(id);
      setDocuments(docs => docs.filter(doc => doc.id !== id));
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
    // Implement search logic
    console.log('Searching:', query);
  };

  const handlePreview = (document: DocumentType) => {
    setSelectedDocument(document);
  };


  const handleUpload = async (files: FileList) => {
    // Early validation
    if (files.length === 0) return;

    setIsLoading(true);
    setProgress(0);
    setLoadingStatus("Preparing files...");

    try {
      // Convert FileList to array for our API
      const fileArray = Array.from(files);
      
      // Upload files using ingestion API
      setLoadingStatus("Uploading files...");
      const uploadedDocs = await ingestionApi.uploadDocuments(fileArray);
      
      // Update progress after upload
      setProgress(50);
      setLoadingStatus("Processing documents...");

      // Wait a bit to show processing state
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Refresh document list
      await fetchDocuments();
      
      // Show success message with count
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
    setDocuments(prevDocs => 
      prevDocs.map(doc => 
        doc.id === updatedDoc.id ? updatedDoc : doc
      )
    );
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
          <DocumentManagementHeader stats={stats} className="flex-shrink-0" />
          <DocumentList
            documents={documents}
            isLoading={isLoading}
            onDelete={handleDelete}
            onSearch={handleSearch}
            onUpload={handleUpload}
            onPreview={handlePreview}
            fetchDocuments={fetchDocuments}
            onDocumentUpdate={handleDocumentUpdate}
          />
        </Card>
      </div>
      <PreviewModal 
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        document={selectedDocument}
        onUpdate={(updatedDoc) => {
          setDocuments(prevDocs => 
            prevDocs.map(doc => 
              doc.id === updatedDoc.id ? updatedDoc : doc
            )
          );
          setSelectedDocument(updatedDoc);
        }}
      />
      <Toaster />
    </div>
  );
};

export default DocumentManagementApp; 