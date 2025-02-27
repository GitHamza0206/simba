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
import { Search, Trash2, Plus, Filter, Eye, FileText, FileSpreadsheet, File, FileCode, FileImage, FolderPlus, Folder, FolderOpen, RefreshCcw, Play, Loader2 } from 'lucide-react';
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
import { ParsingStatusBox } from './ParsingStatusBox';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card"

interface DocumentListProps {
  documents: SimbaDoc[];
  isLoading: boolean;
  onDelete: (id: string) => void;
  onSearch: (query: string) => void;
  onUpload: (files: FileList) => void;
  onPreview: (document: SimbaDoc) => void;
  fetchDocuments: () => Promise<void>;
  onDocumentUpdate: (document: SimbaDoc) => void;
  onParse: (document: SimbaDoc) => void;
  onDisable: (document: SimbaDoc) => void;
  onEnable: (document: SimbaDoc) => void;
}

const PARSING_TASKS_STORAGE_KEY = 'parsing_tasks';

const DocumentList: React.FC<DocumentListProps> = ({
  documents,
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
  
  // Initialize parsingTasks from localStorage
  const [parsingTasks, setParsingTasks] = useState<Record<string, string>>(() => {
    const savedTasks = localStorage.getItem(PARSING_TASKS_STORAGE_KEY);
    return savedTasks ? JSON.parse(savedTasks) : {};
  });
  
  const [parsingButtonStates, setParsingButtonStates] = useState<Record<string, boolean>>({});

  // Save parsingTasks to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(PARSING_TASKS_STORAGE_KEY, JSON.stringify(parsingTasks));
  }, [parsingTasks]);

  // Check status of existing parsing tasks on component mount
  useEffect(() => {
    const checkExistingTasks = async () => {
      const tasks = { ...parsingTasks };
      let hasChanges = false;

      for (const [docId, taskId] of Object.entries(tasks)) {
        try {
          const result = await ingestionApi.getParseStatus(taskId);
          if (result.status === 'SUCCESS' || result.status === 'FAILED') {
            delete tasks[docId];
            hasChanges = true;
            
            // Update document status if task completed
            const doc = documents.find(d => d.id === docId);
            if (doc) {
              const updatedDoc = {
                ...doc,
                metadata: {
                  ...doc.metadata,
                  parsing_status: result.status === 'SUCCESS' ? 'SUCCESS' : 'FAILED'
                }
              };
              onDocumentUpdate(updatedDoc);
            }
          }
        } catch (error) {
          console.error(`Error checking task ${taskId}:`, error);
          delete tasks[docId];
          hasChanges = true;
        }
      }

      if (hasChanges) {
        setParsingTasks(tasks);
      }
    };

    checkExistingTasks();
  }, []);

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

  const handleParseClick = async (document: SimbaDoc) => {
    try {
      // Disable the button during the whole process
      setParsingButtonStates(prev => ({
        ...prev,
        [document.id]: true
      }));

      // If document is enabled, disable it first
      if (document.metadata.enabled) {
        const disabledDoc = {
          ...document,
          metadata: {
            ...document.metadata,
            enabled: false
          }
        };
        onDocumentUpdate(disabledDoc);
        
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const enabledDoc = {
          ...document,
          metadata: {
            ...document.metadata,
            enabled: true,
            parsing_status: 'PENDING'
          }
        };
        onDocumentUpdate(enabledDoc);

        await embeddingApi.delete_document(document.id);
      }

      // Start new parsing task
      const result = await ingestionApi.startParsing(document.id, document.metadata.parser || 'docling');
      setParsingTasks(prev => ({
        ...prev,
        [document.id]: result.task_id
      }));
      
      toast({
        title: document.metadata.parsing_status === 'SUCCESS' ? "Re-parsing Started" : "Parsing Started",
        description: "Document parsing has been queued"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to start parsing",
        variant: "destructive"
      });
    } finally {
      setParsingButtonStates(prev => ({
        ...prev,
        [document.id]: false
      }));
    }
  };

  const handleParseComplete = async (docId: string, status: string) => {
    // Remove the task from parsing tasks and localStorage
    setParsingTasks(prev => {
      const newTasks = { ...prev };
      delete newTasks[docId];
      return newTasks;
    });

    // Update the document's parsing status
    const updatedDoc = documents.find(doc => doc.id === docId);
    if (updatedDoc) {
      const docWithNewStatus = {
        ...updatedDoc,
        metadata: {
          ...updatedDoc.metadata,
          parsing_status: status
        }
      };
      onDocumentUpdate(docWithNewStatus);
    }

    // Show success toast if parsed successfully
    if (status === 'PARSED') {
      toast({
        title: "Success",
        description: "Document parsed successfully",
      });
      // Refresh the document list after successful parsing
      await fetchDocuments();
    }
  };

  const handleParseCancel = async (documentId: string) => {
    // Remove task from tracking and localStorage
    setParsingTasks(prev => {
      const next = { ...prev };
      delete next[documentId];
      return next;
    });
    
    // Refresh documents list
    await fetchDocuments();
    
    toast({
      title: "Cancelled",
      description: "Parsing cancelled",
    });
  };

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Add a new state for tracking the last selected index
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(null);

  // New handler for checkbox clicks to support shift-range selection
  const handleCheckboxClick = (docId: string, index: number, event: React.MouseEvent) => {
    event.stopPropagation();
    const isSelected = selectedIds.has(docId);

    if (event.shiftKey && lastSelectedIndex !== null) {
      // Select range from lastSelectedIndex to current index
      const start = Math.min(lastSelectedIndex, index);
      const end = Math.max(lastSelectedIndex, index);
      const newSet = new Set(selectedIds);
      for (let i = start; i <= end; i++) {
        newSet.add(documents[i].id);
      }
      setSelectedIds(newSet);
    } else {
      // Toggle current selection
      const newSet = new Set(selectedIds);
      if (isSelected) {
        newSet.delete(docId);
      } else {
        newSet.add(docId);
      }
      setSelectedIds(newSet);
      setLastSelectedIndex(index);
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
              <TableHead className="w-8">
                <Checkbox 
                  checked={selectedIds.size === documents.length && documents.length > 0}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setSelectedIds(new Set(documents.map(doc => doc.id)));
                    } else {
                      setSelectedIds(new Set());
                    }
                  }}
                />
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
            
            {documents.map((doc, index) => (
              <TableRow key={doc.id} className="hover:bg-gray-50">
                <TableCell className="w-8">
                  <div onClick={(e) => handleCheckboxClick(doc.id, index, e)}>
                    <Checkbox 
                      checked={selectedIds.has(doc.id)}
                      readOnly
                    />
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {React.createElement(getFileIcon(doc.metadata))}
                    <span>{doc.metadata.filename}</span>
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
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className={cn(
                        doc.metadata.parsing_status === 'SUCCESS' && "bg-green-100 text-green-800 border-green-200",
                        doc.metadata.parsing_status === 'FAILED' && "bg-red-100 text-red-800 border-red-200",
                        doc.metadata.parsing_status === 'PENDING' && "bg-orange-100 text-orange-800 border-orange-200",
                        !doc.metadata.parsing_status && "bg-gray-100 text-gray-800 border-gray-200"
                      )}
                    >
                      {doc.metadata.parsing_status || 'Unparsed'}
                    </Badge>
                    {parsingTasks[doc.id] && (
                      <ParsingStatusBox 
                        taskId={parsingTasks[doc.id]} 
                        onComplete={(status) => handleParseComplete(doc.id, status)}
                        onCancel={() => handleParseCancel(doc.id)}
                      />
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center justify-center gap-2">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            id={`parse-button-${doc.id}`}
                            variant="ghost"
                            size="icon"
                            onClick={(e) => { e.stopPropagation(); handleParseClick(doc); }}
                            className="h-8 w-8"
                            disabled={!!parsingTasks[doc.id] || parsingButtonStates[doc.id]}
                          >
                            {parsingButtonStates[doc.id] ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Play className="h-4 w-4" />
                            )}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{doc.metadata.parsing_status === 'SUCCESS' ? 'Re-parse document' : 'Parse document'}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            id={`enable-button-${doc.id}`}
                            variant="ghost"
                            size="icon"
                            onClick={(e) => { e.stopPropagation(); enableDocument(doc, true); }}
                            className="h-8 w-8"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Enable document</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            id={`disable-button-${doc.id}`}
                            variant="ghost"
                            size="icon"
                            onClick={(e) => { e.stopPropagation(); enableDocument(doc, false); }}
                            className="h-8 w-8 hover:bg-red-100 hover:text-red-600"
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Disable document</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {/* Bottom action bar */}
        {selectedIds.size > 0 && (
          <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white border rounded-lg px-6 py-4 shadow-lg flex justify-between items-center gap-8 z-50">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">
                {selectedIds.size} {selectedIds.size === 1 ? 'document' : 'documents'} selected
              </span>
            </div>
            <div className="flex gap-4">
              <Button 
                size="lg"
                variant="outline"
                onClick={() => {
                  const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));
                  selectedDocs.forEach(doc => handleParseClick(doc));
                }}
              >
                <Play className="h-4 w-4 mr-2" />
                Parse Selected
              </Button>
              <Button 
                size="lg"
                variant="outline"
                onClick={() => {
                  const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));
                  selectedDocs.forEach(doc => {
                    const enableButton = document.querySelector(`#enable-button-${doc.id}`);
                    if (enableButton) {
                      enableButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    }
                  });
                }}
              >
                Enable Selected
              </Button>
              <Button 
                size="lg"
                variant="outline"
                onClick={() => {
                  const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));
                  selectedDocs.forEach(doc => {
                    const disableButton = document.querySelector(`#disable-button-${doc.id}`);
                    if (disableButton) {
                      disableButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    }
                  });
                }}
              >
                Disable Selected
              </Button>
            </div>
          </div>
        )}

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