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
import { Search, Trash2, Plus, Filter, Eye } from 'lucide-react';
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

interface DocumentListProps {
  documents: DocumentType[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  onSearch: (query: string) => void;
  onUpload: (files: FileList) => void;
  onPreview: (document: DocumentType) => void;
  fetchDocuments: () => void;
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
  const [isReindexing, setIsReindexing] = useState(false);

  const formatDate = (dateString: string) => {
    if (dateString === "Unknown") return dateString;
    
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
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
    if (!selectedDocument?.file_path) {
      console.error("Cannot reindex - missing file_path");
      return;
    }

    try {
      console.log("Confirming reindex for document:", {
        id: selectedDocument.id,
        file_path: selectedDocument.file_path,
        parser: selectedDocument.parser,
        parserModified: selectedDocument.parserModified
      });
      
      setIsReindexing(true);
      await reindexDocument(selectedDocument.id, selectedDocument);
      await fetchDocuments();
      setShowReindexDialog(false);
      setSelectedDocument(null);
    } catch (error) {
      console.error('Error reindexing document:', error);
    } finally {
      setIsReindexing(false);
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

  const actions = (document: DocumentType) => (
    console.log("DOCUMENT", document),
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
              <th className="text-left p-4 font-medium text-gray-500">Type</th>
              <th className="text-left p-4 font-medium text-gray-500">Size</th>
              <th className="text-left p-4 font-medium text-gray-500">Uploaded Date</th>
              <th className="text-left p-4 font-medium text-gray-500">Loader</th>
              <th className="text-left p-4 font-medium text-gray-500">Parser</th>
              <th className="text-right p-4 font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {documents.map((document) => (
              <tr 
                key={document.id}
                className="hover:bg-gray-50 transition-colors"
              >
                <td className="p-4 text-sm">{document.name}</td>
                <td className="p-4 text-sm text-gray-500">{document.type}</td>
                <td className="p-4 text-sm text-gray-500">{document.size}</td>
                <td className="p-4 text-sm text-gray-500">{formatDate(document.uploadedAt)}</td>
                <td className={cn(
                  "text-sm",
                  document.loaderModified && "text-red-500"
                )}>
                  <div className={cn(
                    "text-sm",
                    document.loaderModified && "text-red-500"
                  )}>
                    {document.loader}
                  </div>
                </td>
                <td className={cn(
                  "p-4 text-sm",
                  document.parserModified && "text-red-500"
                )}>
                  <div className={cn(
                    "text-sm",
                    document.parserModified && "text-red-500"
                  )}>
                    {document.parser}
                  </div>
                </td>
                <td className="p-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    {actions(document)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

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
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setShowReindexDialog(false)}>
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