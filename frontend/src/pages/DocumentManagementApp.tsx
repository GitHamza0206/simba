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

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      // Fetch both documents and folders
      const [docsResponse, foldersResponse] = await Promise.all([
        ingestionApi.getDocuments(),
        folderApi.getFolders()
      ]);

      // Convert folders to DocumentType format
      const folderDocs: DocumentType[] = foldersResponse.map(folder => ({
        id: folder.id,
        name: folder.name,
        type: 'folder',
        size: '0',
        uploadedAt: folder.created_at,
        content: '',
        loader: '',
        parser: '',
        file_path: folder.path,
        is_folder: true
      }));

      // Combine and sort by name
      const allItems = [...folderDocs, ...docsResponse].sort((a, b) => {
        // Folders first, then sort by name
        if (a.is_folder && !b.is_folder) return -1;
        if (!a.is_folder && b.is_folder) return 1;
        return a.name.localeCompare(b.name);
      });

      setDocuments(allItems);
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast({
        title: "Error",
        description: "Failed to fetch documents and folders",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Chargement initial
  useEffect(() => {
    fetchDocuments();
  }, []); // Suppression de la dépendance toast

  // Rafraîchissement périodique
  useEffect(() => {
    const intervalId = setInterval(() => {
      if (!isLoading) {
        fetchDocuments();
      }
    }, 30000); // Rafraîchir toutes les 30 secondes

    return () => clearInterval(intervalId);
  }, [isLoading]);

  // Simuler la progression pendant le chargement
  useEffect(() => {
    if (isLoading) {
      setProgress(0);
      const timer = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(timer);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      return () => {
        clearInterval(timer);
        setProgress(100); // Mettre à 100% quand le chargement est terminé
      };
    }
  }, [isLoading]);

  const stats: DocumentStatsType = {
    lastQueried: "2 hours ago",
    totalQueries: 145,
    itemsIndexed: documents.filter(doc => !doc.is_folder).length,
    createdAt: "Apr 12, 2024"
  };

  const handleUpload = async (files: FileList) => {
    if (files.length === 0) return;
    if (files.length > 5) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Maximum 5 files allowed at once",
      });
      return;
    }

    setIsLoading(true);
    try {
      const file = files[0];
      if (documents.some(doc => doc.name === file.name)) {
        toast({
          variant: "destructive",
          title: "Error",
          description: "A file with this name already exists",
        });
        return;
      }

      await ingestionApi.uploadDocument(file);
      await fetchDocuments(); // Utiliser la fonction de chargement existante

      toast({
        title: "Success",
        description: "File uploaded successfully",
      });
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error.message || "Upload failed. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

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

  const handleReindex = async (id: string) => {
    try {
      setIsLoading(true);
      setProgress(0);

      // Get the current document
      const doc = documents.find(d => d.id === id);
      if (!doc) {
        throw new Error("Document not found");
      }

      // Use the reindexDocument function from parsing_api
      const reindexedDoc = await reindexDocument(
        id, 
        doc,
        (status, progress) => {
          setProgress(progress);
          setLoadingStatus(status);
          // Show toast for key progress points
          if (progress === 100) {
            toast({
              title: "Success",
              description: "Document reindexed successfully",
            });
          }
        }
      );

      // Refresh documents list
      await fetchDocuments();
      
      // Update the document in the list with the reindexed version
      setDocuments(prevDocs => 
        prevDocs.map(d => 
          d.id === id ? reindexedDoc : d
        )
      );

    } catch (error: unknown) {
      console.error('Error reindexing document:', error);
      const errorMessage = error instanceof Error ? error.message : "Failed to reindex document";
      
      // Handle specific error cases
      if (errorMessage.includes("not found")) {
        // Document or file not found - remove it from the list
        setDocuments(docs => docs.filter(doc => doc.id !== id));
        toast({
          variant: "destructive",
          title: "Document Not Found",
          description: "The document was not found and has been removed from the list",
        });
      } else {
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage,
        });
      }
    } finally {
      setIsLoading(false);
      setProgress(0);
    }
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