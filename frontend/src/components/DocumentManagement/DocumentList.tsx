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
import { Search, Trash2, Plus, Filter, Eye, FileText, FileSpreadsheet, File, FileCode, FileImage, FolderPlus, Folder, FolderOpen } from 'lucide-react';
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

interface DocumentListProps {
  documents: DocumentType[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  onSearch: (query: string) => void;
  onUpload: (files: FileList) => void;
  onPreview: (document: DocumentType) => void;
  fetchDocuments: () => Promise<void>;
}

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  isLoading,
  onDelete,
  onSearch,
  onUpload,
  onPreview,
  fetchDocuments,
}) => {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [showReindexDialog, setShowReindexDialog] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentType | null>(null);
  const [reindexProgress, setReindexProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState("");
  const [isReindexing, setIsReindexing] = useState(false);
  const [showCreateFolderDialog, setShowCreateFolderDialog] = useState(false);
  const [currentPath, setCurrentPath] = useState('/');
  const [uploadDir, setUploadDir] = useState<string>('');
  const { toast } = useToast();

  useEffect(() => {
    const fetchUploadDir = async () => {
      try {
        const path = await ingestionApi.getUploadDirectory();
        setUploadDir(path);
      } catch (error) {
        console.error('Failed to fetch upload directory:', error);
      }
    };

    fetchUploadDir();
  }, []);

  const formatDate = (dateString: string) => {
    if (dateString === "Unknown") return dateString;
    
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const formatFileSize = (size: string) => {
    // Remove any existing 'MB' suffix first
    const cleanSize = size.replace(/\s*MB\s*/gi, '');
    
    // Convert to number
    const bytes = parseFloat(cleanSize);
    if (isNaN(bytes)) return '0 MB';
    
    // Convert to MB with more precision (4 decimal places)
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const handleReindexClick = (document: DocumentType) => {
    if (!document.file_path) {
      console.error("Document missing file_path:", document);
      return;
    }
    
    console.log("Document to reindex:", {
      id: document.id,
      file_path: document.file_path,
      parser: document.parser,
      parserModified: document.parserModified
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
        selectedDocument.parser,
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

  const getReindexWarningContent = (document: DocumentType) => {
    if (document.loaderModified && document.parserModified) {
      return {
        title: "Confirm Re-indexing",
        description: "This will update both the loader and parser. Changing the parser will create a new markdown file. Are you sure you want to proceed?"
      };
    } else if (document.parserModified) {
      return {
        title: "Confirm Parser Change",
        description: "Changing the parser will create a new markdown file. Are you sure you want to proceed?"
      };
    } else if (document.loaderModified) {
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

  const getFileIcon = (fileType: string) => {
    const type = fileType.toLowerCase();
    
    switch (type) {
      case '.pdf':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case '.xlsx':
      case '.xls':
      case '.csv':
        return <FileSpreadsheet className="h-4 w-4 text-green-500" />;
      case '.md':
      case '.markdown':
        return <FileCode className="h-4 w-4 text-purple-500" />;
      case '.docx':
      case '.doc':
        return <FileText className="h-4 w-4 text-blue-400" />;
      case '.txt':
        return <FileText className="h-4 w-4 text-gray-500" />;
      case '.jpg':
      case '.jpeg':
      case '.png':
        return <FileImage className="h-4 w-4 text-orange-500" />;
      default:
        return <File className="h-4 w-4 text-gray-500" />;
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

  const renderTableRow = (item: DocumentType) => {
    if (item.is_folder) {
      return (
        <TableRow key={item.id} className="hover:bg-gray-50">
          <TableCell className="p-4">
            <div className="flex items-center gap-2">
              <Folder className="h-4 w-4 text-blue-500" />
              <span>{item.name}</span>
            </div>
          </TableCell>
          <TableCell className="p-4">-</TableCell>
          <TableCell className="p-4">-</TableCell>
          <TableCell className="p-4">-</TableCell>
          <TableCell className="p-4">-</TableCell>
          <TableCell className="p-4 text-right">
            <div className="flex justify-end gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onDelete(item.id)}
                title="Delete folder"
                className="hover:bg-red-100 hover:text-red-600"
              >
                <Trash2 className="h-4 w-4 text-red-500" />
              </Button>
            </div>
          </TableCell>
        </TableRow>
      );
    }

    return (
      <TableRow key={item.id} className="hover:bg-gray-50">
        <TableCell className="p-4">
          <div className="flex items-center gap-2">
            {getFileIcon(item.type)}
            <span>{item.name}</span>
          </div>
        </TableCell>
        <TableCell className="p-4">{formatFileSize(item.size)}</TableCell>
        <TableCell className="p-4">{formatDate(item.uploadedAt)}</TableCell>
        <TableCell className="p-4">{item.loader}</TableCell>
        <TableCell className="p-4">{item.parser}</TableCell>
        <TableCell className="p-4 text-right">
          <div className="flex justify-end gap-2">
            {(item.loaderModified || item.parserModified) && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleReindexClick(item)}
                className="bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-700"
              >
                Re-index
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onPreview(item)}
              title="Preview document"
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onDelete(item.id)}
              title="Delete document"
              className="hover:bg-red-100 hover:text-red-600"
            >
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </div>
        </TableCell>
      </TableRow>
    );
  };

  return (
    <div className="relative">
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="flex-1 relative">
            <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              onChange={(e) => onSearch(e.target.value)}
              className="h-9 w-full pl-9"
            />
          </div>
          <div className="flex items-center space-x-2 flex-shrink-0">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-9"
                    onClick={() => fetchDocuments()}
                  >
                    <RotateCw className="h-4 w-4 mr-2" />
                    Sync DB
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sync vector database</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Button
              variant="outline"
              size="sm"
              className="h-9"
              onClick={() => setShowCreateFolderDialog(true)}
            >
              <FolderPlus className="h-4 w-4 mr-2" />
              New Folder
            </Button>
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
              <TableHead>Name</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Upload Date</TableHead>
              <TableHead>Loader</TableHead>
              <TableHead>Parser</TableHead>
              <TableHead className="text-right">Actions</TableHead>
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
            
            {documents.map((item) => renderTableRow(item))}
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