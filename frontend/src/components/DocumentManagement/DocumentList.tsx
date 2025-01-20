import React, { useState } from 'react';
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
import { Search, Trash2, Plus, Filter, Eye, FileText, FileSpreadsheet, File, FileCode, FileImage, FolderPlus, Folder } from 'lucide-react';
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
import { reindexDocument } from '@/lib/parsing_api';
import { Progress } from "@/components/ui/progress"
import { useToast } from "@/hooks/use-toast";
import { CreateFolderDialog } from './CreateFolderDialog';
import { folderApi } from '@/lib/folder_api';

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
  const { toast } = useToast();

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
      await reindexDocument(
        selectedDocument.id, 
        selectedDocument,
        (status, progress) => {
          setProgressStatus(status);
          setReindexProgress(progress);
        }
      );
      toast({
        title: "Success",
        description: "Document reindexed successfully",
      });
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

  const actions = (document: DocumentType) => (

    <div className="flex gap-2">
      {(document.loaderModified || document.parserModified) && (
        <Button
          variant="secondary"
          size="sm"
          onClick={() => handleReindexClick(document)}
          className="bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-700"
        >
          Re-index
        </Button>
      )}

      <Button
        variant="ghost"
        size="icon"
        onClick={() => onPreview(document)}
        title="Preview document"
      >
        <Eye className="h-4 w-4" />
      </Button>
      
      <Button
        variant="ghost"
        size="icon"
        onClick={() => onDelete(document.id)}
        title="Delete document"
        className="hover:bg-red-100 hover:text-red-600"
      >
        <Trash2 className="h-4 w-4 text-red-500" />
      </Button>
    </div>
  );

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
        <tr key={item.id} className="hover:bg-gray-50">
          <td className="p-4">
            <div className="flex items-center gap-2">
              <Folder className="h-4 w-4 text-blue-500" />
              <span>{item.name}</span>
            </div>
          </td>
          <td className="p-4" colSpan={3}></td>
          <td className="p-4 text-right">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onDelete(item.id)}
              title="Delete folder"
              className="hover:bg-red-100 hover:text-red-600"
            >
              <Trash2 className="h-4 w-4 text-red-500" />
            </Button>
          </td>
        </tr>
      );
    }

    return (
      <tr key={item.id} className="hover:bg-gray-50">
        <td className="p-4">
          <div className="flex items-center gap-2">
            {getFileIcon(item.type)}
            <span>{item.name}</span>
          </div>
        </td>
        <td className="p-4">{formatFileSize(item.size)}</td>
        <td className="p-4">{formatDate(item.uploadedAt)}</td>
        <td className="p-4">{item.loader}</td>
        <td className="p-4">{item.parser}</td>
        <td className="p-4 text-right">
          {actions(item)}
        </td>
      </tr>
    );
  };

  return (
    <div className="flex-1 flex flex-col">
      <div className="p-4 border-b flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 w-4 h-4" />
            <Input
              placeholder="Search documents..."
              className="pl-10"
              onChange={(e) => onSearch(e.target.value)}
            />
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Filter className="w-4 h-4 mr-2" />
                File type
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>PDF</DropdownMenuItem>
              <DropdownMenuItem>Word</DropdownMenuItem>
              <DropdownMenuItem>Text</DropdownMenuItem>
              <DropdownMenuItem>Markdown</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button
            onClick={() => setShowCreateFolderDialog(true)}
            variant="outline"
            className="gap-2"
          >
            <FolderPlus className="w-4 h-4" />
            New Folder
          </Button>
          <Button 
            onClick={() => setIsUploadModalOpen(true)}
            className="bg-primary hover:bg-primary/90"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Document
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-white z-10">
            <tr>
              <th className="text-left p-4 font-medium text-gray-500">Name</th>
              <th className="text-left p-4 font-medium text-gray-500">Size</th>
              <th className="text-left p-4 font-medium text-gray-500">Created Date</th>
              <th className="text-left p-4 font-medium text-gray-500">Loader</th>
              <th className="text-left p-4 font-medium text-gray-500">Parser</th>
              <th className="text-right p-4 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map(renderTableRow)}
          </tbody>
        </table>
      </div>

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
    </div>
  );
};

export default DocumentList;