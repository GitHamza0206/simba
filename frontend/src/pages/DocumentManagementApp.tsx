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

const DocumentManagementApp: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { toast } = useToast();
  const [previewContent, setPreviewContent] = useState<string>("");
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentType | null>(null);

  // Fonction de chargement des documents
  const fetchDocuments = async () => {
    try {
      const docs = await ingestionApi.getDocuments();
      if (!docs || docs.length === 0) {
        setDocuments([]);
        return;
      }
      setDocuments(docs);
    } catch (error: any) {
      console.error('Error fetching documents:', error);
      setDocuments([]);
      toast({
        variant: "destructive",
        title: "Error",
        description: error.message || "Failed to fetch documents",
      });
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
    itemsIndexed: documents.length,
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

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 p-6">
        {isLoading && (
          <div className="fixed inset-0 bg-background/50 backdrop-blur-sm flex flex-col gap-4 items-center justify-center z-50">
            <Progress value={progress} className="w-[60%] max-w-md" />
            <p className="text-sm text-muted-foreground">Loading documents... {progress}%</p>
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
            
          />
        </Card>
      </div>
      <PreviewModal 
        isOpen={!!selectedDocument}
        onClose={() => setSelectedDocument(null)}
        document={selectedDocument}
      />
      <Toaster />
    </div>
  );
};

export default DocumentManagementApp; 