import React, { useState, useEffect } from 'react';
import { CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { DocumentType } from '@/types/document';
import { Search, Trash2, Plus, Filter, Eye, FileText, FileSpreadsheet, File, FileCode, FileImage, FolderPlus, Folder, FolderOpen, RefreshCcw, Play } from 'lucide-react';
import { Button } from '../ui/button';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { FileUploadModal } from './FileUploadModal';
import { cn } from '@/lib/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/hooks/use-toast";
import { CreateFolderDialog } from './CreateFolderDialog';
import { folderApi } from '@/lib/folder_api';
import { RotateCw } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { ingestionApi } from '@/lib/ingestion_api';
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { SimbaDoc } from '@/types/document';
import { Metadata } from '@/types/document';
import { embeddingApi } from '@/lib/embedding_api';

interface DocumentListProps {
  documents: SimbaDoc[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  onSearch: (query: string) => void;
  onUpload: (files: FileList) => void;
  onPreview: (document: SimbaDoc) => void;
  fetchDocuments: () => Promise<void>;
  onDocumentUpdate: (document: SimbaDoc) => void;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  isLoading,
  onDelete,
  onSearch,
  onUpload,
  onPreview,
  fetchDocuments,
  onDocumentUpdate,
}) => {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [showReindexDialog, setShowReindexDialog] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<SimbaDoc | null>(null);
  const [reindexProgress, setReindexProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState("");
  const [isReindexing, setIsReindexing] = useState(false);
  const [showCreateFolderDialog, setShowCreateFolderDialog] = useState(false);
  const [currentPath, setCurrentPath] = useState('/');
  const [uploadDir, setUploadDir] = useState<string>('');
  const { toast } = useToast();
  const [enabledDocuments, setEnabledDocuments] = useState<Set<string>>(
    new Set(documents.filter(doc => doc.metadata.enabled).map(doc => doc.id))
  );

  useEffect(() => {
    setEnabledDocuments(
      new Set(documents.filter(doc => doc.metadata.enabled).map(doc => doc.id))
    );
  }, [documents]);

  const formatDate = (dateString: string) => {
    if (dateString === "Unknown") return dateString;
    
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleReindexClick = (document: SimbaDoc) => {
    if (!document.metadata.file_path) {
      console.error("Document missing file_path:", document);
      return;
    }
    
    console.log("Document to reindex:", {
      id: document.id,
      file_path: document.metadata.file_path,
      parser: document.metadata.parser,
      parserModified: document.metadata.parserModified
    });
    
    setSelectedDocument(document);
    setShowReindexDialog(true);
  };

  const handleReindexConfirm = async () => {
    if (!selectedDocument) return;
    
    setIsReindexing(true);
    try {
      await ingestionApi.reindexDocument(
        selectedDocument.id, 
        selectedDocument.metadata.parser,
        (status, progress) => {
          setProgressStatus(status);
          setReindexProgress(progress);
        }
      );
      toast({
        title: "Success",
        description: "Document reindexed successfully",
      });
      await fetchDocuments();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to reindex document",
        variant: "destructive",
      });
    } finally {
      setIsReindexing(false);
      setShowReindexDialog(false);
      setReindexProgress(0);
      setProgressStatus("");
    }
  };

  const getReindexWarningContent = (document: SimbaDoc) => {
    if (document.metadata.loaderModified && document.metadata.parserModified) {
      return {
        title: "Confirm Re-indexing",
        description: "This will update both the loader and parser. Changing the parser will create a new markdown file. Are you sure you want to proceed?"
      };
    } else if (document.metadata.parserModified) {
      return {
        title: "Confirm Parser Change",
        description: "Changing the parser will create a new markdown file. Are you sure you want to proceed?"
      };
    } else if (document.metadata.loaderModified) {
      return {
        title: "Confirm Loader Change",
        description: "Do you want to update the document loader?"
      };
    }
    return {
      title: "Re-index Document",
      description: "Are you sure you want to re-index this document?"
    };
  };

  const getFileIcon = (metadata: Metadata) => {
    if (metadata.is_folder) return Folder;
    
    const extension = metadata.file_path.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return FileText;
      case 'xlsx':
      case 'xls':
      case 'csv':
        return FileSpreadsheet;
      case 'md':
      case 'markdown':
        return FileCode;
      case 'docx':
      case 'doc':
        return FileText;
      case 'txt':
        return FileText;
      case 'jpg':
      case 'jpeg':
      case 'png':
        return FileImage;
      default:
        return File;
    }
  };

  const handleCreateFolder = async (folderName: string) => {
    try {
      await folderApi.createFolder(folderName, currentPath);
      toast({
        title: "Success",
        description: `Folder "${folderName}" created successfully`,
      });
      await fetchDocuments();
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create folder",
        variant: "destructive",
      });
    }
  };

  const enableDocument = async (doc: SimbaDoc, checked: boolean) => {
    try {
      // Update local state immediately for better UX
      const updatedDoc = { ...doc, metadata: { ...doc.metadata, enabled: checked }};
      onDocumentUpdate(updatedDoc);

      if (!checked) {  // If we're disabling the document
        // Call delete endpoint
        await embeddingApi.delete_document(doc.id);
        
        setEnabledDocuments(prev => {
          const next = new Set(prev);
          next.delete(doc.id);
          return next;
        });
        
        toast({
          title: "Document removed",
          description: "Document removed from embeddings successfully"
        });
      } else {  // If we're enabling the document
        // Call embed endpoint
        await embeddingApi.embedd_document(doc.id);
        
        setEnabledDocuments(prev => {
          const next = new Set(prev);
          next.add(doc.id);
          return next;
        });
        
        toast({
          title: "Document embedded",
          description: `Document embedded successfully.`
        });
      }
    } catch (error) {
      // Revert local state on error
      const revertedDoc = { ...doc, metadata: { ...doc.metadata, enabled: !checked }};
      onDocumentUpdate(revertedDoc);
      
      setEnabledDocuments(prev => {
        const next = new Set(prev);
        checked ? next.delete(doc.id) : next.add(doc.id);
        return next;
      });
      
      toast({
        title: "Error",
        description: error instanceof Error 
          ? error.message 
          : `Failed to ${checked ? 'embed' : 'remove'} document`,
        variant: "destructive"
      });
    }
  };

  const handleDeleteEmbedding = async (docIds: string[]) => {
    try {
      await embeddingApi.delete_document(docIds);
      setEnabledDocuments(prev => {
        const next = new Set(prev);
        docIds.forEach(id => next.delete(id));
        return next;
      });
      toast({
        title: "Success",
        description: docIds.length > 1 
          ? "Document embeddings deleted successfully" 
          : "Document embedding deleted successfully"
      });
      await fetchDocuments();
    } catch (error) {
      console.error('Error deleting embeddings:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to delete document embeddings",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="relative">
      <CardContent>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Input
              placeholder="Search documents..."
              className="h-9 w-[200px]"
              onChange={(e) => onSearch(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-9"
                    onClick={fetchDocuments}
                  >
                    <RefreshCcw className={cn(
                      "h-4 w-4 mr-2",
                      isLoading && "animate-spin"
                    )} />
                    Refresh
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Refresh document list</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button
              variant="default"
              size="sm"
              className="h-9"
              onClick={() => setIsUploadModalOpen(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              Upload
            </Button>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[30px]">
                <Checkbox />
              </TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Chunk Number</TableHead>
              <TableHead>Upload Date</TableHead>
              <TableHead>Enable</TableHead>
              <TableHead>Parsing Status</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow className="h-8 text-xs border-b border-muted">
              <TableCell colSpan={6}>
                <div className="flex items-center text-muted-foreground">
                  <FolderOpen className="h-3 w-3 mr-1" />
                  <code className="text-[10px]">{uploadDir}</code>
                </div>
              </TableCell>
            </TableRow>
            
            {documents.map((doc) => (
              <TableRow key={doc.id} className="hover:bg-gray-50">
                <TableCell>
                  <Checkbox />
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {React.createElement(getFileIcon(doc.metadata))}
                    <span>{doc.metadata.file_path.split('/').pop()}</span>
                  </div>
                </TableCell>
                <TableCell>
                  {doc.metadata.enabled ? doc.documents.length : 0}
                </TableCell>
                <TableCell>{formatDate(doc.metadata.uploadedAt || "Unknown")}</TableCell>
                <TableCell>
                  <Switch
                    checked={doc.metadata.enabled}
                    onCheckedChange={(checked) => enableDocument(doc, checked)}
                    aria-label="Toggle document embedding"
                  />
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      doc.metadata.parsing_status === 'SUCCESS' ? 'success' :
                      doc.metadata.parsing_status === 'CANCEL' ? 'warning' :
                      doc.metadata.parsing_status === 'FAILED' ? 'destructive' :
                      'default'
                    }
                  >
                    {doc.metadata.parsing_status || 'PENDING'}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleParseClick(doc)}
                            className="h-8 w-8"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Parse document</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onPreview(doc)}
                            className="h-8 w-8"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Preview document</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onDelete(doc.id)}
                            className="h-8 w-8 hover:bg-red-100 hover:text-red-600"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Delete document</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        <CreateFolderDialog
          isOpen={showCreateFolderDialog}
          onClose={() => setShowCreateFolderDialog(false)}
          onCreateFolder={handleCreateFolder}
          currentPath={currentPath}
        />

        <FileUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUpload={onUpload}
        />

        <AlertDialog 
          open={showReindexDialog} 
          onOpenChange={setShowReindexDialog}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                {selectedDocument && getReindexWarningContent(selectedDocument).title}
              </AlertDialogTitle>
              <AlertDialogDescription>
                {selectedDocument && getReindexWarningContent(selectedDocument).description}
              </AlertDialogDescription>
            </AlertDialogHeader>
            
            {isReindexing && (
              <div className="space-y-2 my-4">
                <div className="text-sm text-muted-foreground">
                  {progressStatus}
                </div>
                <Progress value={reindexProgress} className="w-full" />
              </div>
            )}
            
            <AlertDialogFooter>
              <AlertDialogCancel 
                onClick={() => setShowReindexDialog(false)}
                disabled={isReindexing}
              >
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction 
                onClick={handleReindexConfirm}
                className="bg-primary text-white hover:bg-primary/90"
                disabled={isReindexing}
              >
                {isReindexing ? "Processing..." : "Proceed"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </CardContent>
    </div>
  );
};

export default DocumentList;