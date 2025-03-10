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
import { Search, Trash2, Plus, Filter, Eye, FileText, FileSpreadsheet, File, FileCode, FileImage, FolderPlus, Folder, FolderOpen, RefreshCcw, Play, Loader2, Pencil, CheckCircle, Settings } from 'lucide-react';
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
import { embeddingApi } from '@/lib/api_services';
import { ingestionApi } from '@/lib/ingestion_api';
import { parsingApi } from '@/lib/parsing_api';
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { SimbaDoc, Metadata } from '@/types/document';
import { ParsingStatusBox } from './ParsingStatusBox';
import { ParserConfigModal } from './ParserConfigModal';
import { ParserConfigDebug } from './ParserConfigDebug';
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface Folder {
  id: string;
  name: string;
  parentId: string | null;
}

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
const FOLDERS_STORAGE_KEY = 'document_folders';

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
  
  // Add state to track newly uploaded files that should be associated with folders
  const [pendingUploads, setPendingUploads] = useState<Record<string, string>>({});
  
  // Initialize parsingTasks from localStorage
  const [parsingTasks, setParsingTasks] = useState<Record<string, string>>(() => {
    const savedTasks = localStorage.getItem(PARSING_TASKS_STORAGE_KEY);
    return savedTasks ? JSON.parse(savedTasks) : {};
  });
  
  const [parsingButtonStates, setParsingButtonStates] = useState<Record<string, boolean>>({});

  // Add state for available parsers
  const [availableParsers, setAvailableParsers] = useState<string[]>(["docling"]);

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

  // Add useEffect to handle associating newly uploaded documents with folders
  useEffect(() => {
    // This will run when documents array changes (e.g., after new uploads)
    if (Object.keys(pendingUploads).length > 0 && documents.length > 0) {
      // Iterate through pending uploads and check if the documents are loaded
      const pendingCopy = { ...pendingUploads };
      let hasChanges = false;
      
      // Load existing folder associations
      const associations = loadDocumentFolderAssociations();
      
      documents.forEach(doc => {
        // If this document has a pending folder assignment
        if (pendingUploads[doc.id]) {
          // This is a frontend-only operation since we don't have backend folder support
          // In a real app, you would update the document's folder_id in the backend
          console.log(`Associating document ${doc.id} with folder ${pendingUploads[doc.id]}`);
          
          // Update the document with the folder_id
          const updatedDoc = {
            ...doc,
            metadata: {
              ...doc.metadata,
              folder_id: pendingUploads[doc.id]
            }
          };
          
          // Save the folder association to localStorage
          associations[doc.id] = pendingUploads[doc.id];
          
          // Update the document in parent component
          onDocumentUpdate(updatedDoc);
          
          // Remove from pending uploads
          delete pendingCopy[doc.id];
          hasChanges = true;
        }
      });
      
      if (hasChanges) {
        setPendingUploads(pendingCopy);
        saveDocumentFolderAssociations(associations);
      }
    }
  }, [documents, pendingUploads, onDocumentUpdate]);

  // Add useEffect to fetch available parsers
  useEffect(() => {
    const fetchParsers = async () => {
      try {
        const parsers = await parsingApi.getParsers();
        setAvailableParsers(parsers);
      } catch (error) {
        console.error("Failed to fetch available parsers:", error);
        setAvailableParsers(["docling"]); // Fallback to docling
      }
    };

    fetchParsers();
  }, []);

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

  const [isRenamingId, setIsRenamingId] = useState<string | null>(null);
  const [newFolderName, setNewFolderName] = useState("");
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [draggedDocId, setDraggedDocId] = useState<string | null>(null);

  // Initialize folders from localStorage
  const [folders, setFolders] = useState<Folder[]>(() => {
    const savedFolders = localStorage.getItem(FOLDERS_STORAGE_KEY);
    return savedFolders ? JSON.parse(savedFolders) : [];
  });

  // Save folders to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(FOLDERS_STORAGE_KEY, JSON.stringify(folders));
  }, [folders]);

  // Store document folder associations in localStorage
  const DOCUMENT_FOLDERS_KEY = 'document_folder_associations';
  
  // Save document folder associations to localStorage
  const saveDocumentFolderAssociations = (associations: Record<string, string | null>) => {
    localStorage.setItem(DOCUMENT_FOLDERS_KEY, JSON.stringify(associations));
  };
  
  // Load document folder associations from localStorage
  const loadDocumentFolderAssociations = (): Record<string, string | null> => {
    const saved = localStorage.getItem(DOCUMENT_FOLDERS_KEY);
    return saved ? JSON.parse(saved) : {};
  };
  
  // Update document folder associations when documents change
  useEffect(() => {
    // Skip if no documents
    if (documents.length === 0) return;
    
    // Load existing associations
    const associations = loadDocumentFolderAssociations();
    let hasChanges = false;
    
    // Update associations with current document folder_ids
    documents.forEach(doc => {
      if (doc.metadata.folder_id) {
        associations[doc.id] = doc.metadata.folder_id;
        hasChanges = true;
      }
    });
    
    if (hasChanges) {
      saveDocumentFolderAssociations(associations);
    }
  }, [documents]);
  
  // Apply folder associations to documents after fetching
  useEffect(() => {
    // Skip if no documents
    if (documents.length === 0) return;
    
    // Load associations
    const associations = loadDocumentFolderAssociations();
    let hasUpdates = false;
    
    // Check each document to see if it needs a folder_id update
    const updatedDocs = documents.map(doc => {
      // If document has an association but no folder_id, update it
      if (associations[doc.id] && !doc.metadata.folder_id) {
        hasUpdates = true;
        return {
          ...doc,
          metadata: {
            ...doc.metadata,
            folder_id: associations[doc.id]
          }
        };
      }
      return doc;
    });
    
    // Update documents if needed
    if (hasUpdates) {
      updatedDocs.forEach(doc => {
        if (doc.metadata.folder_id) {
          onDocumentUpdate(doc);
        }
      });
    }
  }, [documents, onDocumentUpdate]);

  // Frontend-only folder operations
  const handleCreateFolder = () => {
    const newFolder: Folder = {
      id: Math.random().toString(36).substr(2, 9),
      name: newFolderName,
      parentId: currentFolderId
    };
    setFolders([...folders, newFolder]);
    setNewFolderName("");
    setShowCreateFolderDialog(false);
    toast({
      title: "Success",
      description: "Folder created"
    });
  };

  const handleRenameFolder = (folderId: string, newName: string) => {
    setFolders(folders.map(folder => 
      folder.id === folderId ? { ...folder, name: newName } : folder
    ));
    setIsRenamingId(null);
    toast({
      title: "Success",
      description: "Folder renamed successfully"
    });
  };

  const handleRenameDocument = (docId: string, newName: string) => {
    // Check if it's a folder
    const folder = folders.find(f => f.id === docId);
    if (folder) {
      handleRenameFolder(docId, newName);
      return;
    }
    
    // For regular documents - show toast for now
    setIsRenamingId(null);
    toast({
      title: "Info",
      description: "Document renaming will be implemented with backend support"
    });
  };

  // Modify handleUpload to capture the current folder
  const handleUpload = (files: FileList) => {
    // First create a record of files that will be uploaded
    const fileNames = Array.from(files).map(file => file.name);
    
    // Call the parent's onUpload function
    onUpload(files);
    
    // Track that these files should be associated with the current folder
    if (currentFolderId) {
      // Generate a unique identifier for this upload batch
      const uploadBatchId = Date.now().toString();
      
      toast({
        title: "Files uploading",
        description: `Uploading to folder: ${folders.find(f => f.id === currentFolderId)?.name || 'Unknown'}`
      });
      
      // Check for new documents more frequently and for a longer period
      let checkAttempts = 0;
      const maxAttempts = 10; // Try up to 10 times
      
      const checkForNewUploads = () => {
        // Find newly uploaded documents matching our filenames
        const newlyUploaded = documents.filter(doc => {
          // Skip documents that already have a folder_id
          if (doc.metadata.folder_id) return false;
          
          // Skip folders
          if (doc.metadata.is_folder) return false;
          
          // Check if the filename matches one we just uploaded
          return fileNames.some(name => doc.metadata.filename === name);
        });
        
        // Associate these documents with the current folder
        if (newlyUploaded.length > 0) {
          console.log(`Found ${newlyUploaded.length} new uploads to associate with folder ${currentFolderId}`);
          
          const updates: Record<string, string> = {};
          
          newlyUploaded.forEach(doc => {
            updates[doc.id] = currentFolderId;
          });
          
          // Add these to pending uploads
          setPendingUploads(prev => ({
            ...prev,
            ...updates
          }));
          
          // If we found some documents, but not all, continue checking
          if (newlyUploaded.length < fileNames.length && checkAttempts < maxAttempts) {
            checkAttempts++;
            setTimeout(checkForNewUploads, 1000);
          }
        } else if (checkAttempts < maxAttempts) {
          // If we didn't find any yet, keep checking
          checkAttempts++;
          setTimeout(checkForNewUploads, 1000);
        }
      };
      
      // Start checking for new uploads after a short delay
      setTimeout(checkForNewUploads, 500);
    }
  };

  // Modify getCurrentFolderDocuments to show files uploaded to current folder
  const getCurrentFolderDocuments = () => {
    // Filter real documents that are in the current folder
    const filteredDocs = documents.filter(doc => {
      // Skip folder items
      if (doc.metadata.is_folder) return false;
      
      // If we're at root level and document doesn't have a folder_id, show it
      if (currentFolderId === null) {
        return !doc.metadata.folder_id;
      }
      
      // If document has a folder_id matching current folder, show it
      return doc.metadata.folder_id === currentFolderId;
    });
    
    // Create folder items that should be in the current folder
    const folderItems = folders
      .filter(folder => folder.parentId === currentFolderId)
      .map(folder => ({
        id: folder.id,
        metadata: {
          filename: folder.name,
          is_folder: true,
          enabled: false,
          file_path: `/${folder.name}`,
          parsing_status: '',
          uploadedAt: new Date().toISOString(),
          type: 'folder'  // Add type property to satisfy TypeScript
        },
        documents: [],
        chunks: []
      } as SimbaDoc)); 
    
    // Combine and return folders first, then documents
    return [...folderItems, ...filteredDocs];
  };

  // Get folder path for display
  const getFolderPath = (folderId: string | null): string => {
    if (!folderId) return '/';
    
    // Build full path by traversing up the folder tree
    const buildPath = (id: string, path: string = ''): string => {
      const folder = folders.find(f => f.id === id);
      if (!folder) return path;
      
      const currentPath = `/${folder.name}${path}`;
      
      if (folder.parentId) {
        return buildPath(folder.parentId, currentPath);
      }
      
      return currentPath;
    };
    
    return buildPath(folderId);
  };

  // Get breadcrumb navigation
  const getBreadcrumbs = () => {
    if (!currentFolderId) return [{ id: null, name: 'Home' }];
    
    const result: Array<{ id: string | null, name: string }> = [{ id: null, name: 'Home' }];
    let current = folders.find(f => f.id === currentFolderId);
    
    // For the current folder
    if (current) {
      result.push({ id: current.id, name: current.name });
    }
    
    // Build breadcrumbs in reverse order (from current to root)
    while (current && current.parentId) {
      const parent = folders.find(f => f.id === current!.parentId);
      if (parent) {
        // Insert after Home but before other crumbs
        result.splice(1, 0, { id: parent.id, name: parent.name });
        current = parent;
      } else {
        break;
      }
    }
    
    return result;
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
      const result = await parsingApi.startParsing(document.id, document.metadata.parser || 'docling');
      
      // If we got a SimbaDoc directly (from Mistral OCR)
      if (result && 'id' in result && 'metadata' in result) {
        console.log('Received parsed document directly:', result);
        
        // Update the document in state
        onDocumentUpdate(result);
        
        toast({
          title: "Parsing Complete",
          description: `Document parsed successfully with ${document.metadata.parser || 'docling'}`
        });
      }
      // Otherwise handle as an async task (docling)
      else if ('task_id' in result && result.task_id) {
        setParsingTasks(prev => ({
          ...prev,
          [document.id]: result.task_id as string
        }));
        
        toast({
          title: document.metadata.parsing_status === 'SUCCESS' ? "Re-parsing Started" : "Parsing Started",
          description: "Document parsing has been queued"
        });
      }
      else {
        console.error('Unexpected parsing response:', result);
        toast({
          title: "Error",
          description: "Received unexpected response from parsing service",
          variant: "destructive"
        });
      }
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
      // Get the folder association from localStorage
      const associations = loadDocumentFolderAssociations();
      const folderId = associations[docId] || updatedDoc.metadata.folder_id;
      
      const docWithNewStatus = {
        ...updatedDoc,
        metadata: {
          ...updatedDoc.metadata,
          parsing_status: status,
          folder_id: folderId // Ensure folder_id is preserved
        }
      };
      
      onDocumentUpdate(docWithNewStatus);
      
      // Make sure the association is saved
      if (folderId) {
        associations[docId] = folderId;
        saveDocumentFolderAssociations(associations);
      }
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

  // When clicking on a folder
  const handleFolderClick = (folderId: string) => {
    setCurrentFolderId(folderId);
  };

  // To navigate back to parent folder
  const navigateToParent = () => {
    if (currentFolderId === null) return;
    
    const currentFolder = folders.find(f => f.id === currentFolderId);
    setCurrentFolderId(currentFolder?.parentId || null);
  };

  // Add delete folder functionality
  const handleDeleteFolder = (folderId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    // Check if folder is empty
    const hasDocuments = documents.some(doc => doc.metadata.folder_id === folderId);
    const hasSubfolders = folders.some(folder => folder.parentId === folderId);
    
    if (hasDocuments || hasSubfolders) {
      toast({
        title: "Cannot Delete Folder",
        description: "Folder is not empty. Please move or delete all items first.",
        variant: "destructive"
      });
      return;
    }
    
    // Remove the folder
    setFolders(folders.filter(f => f.id !== folderId));
    toast({
      title: "Success",
      description: "Folder deleted successfully"
    });
  };

  // For drag and drop folder functionality
  const handleDragOver = (doc: SimbaDoc, e: React.DragEvent) => {
    if (doc.metadata.is_folder) {
      e.preventDefault();
      e.currentTarget.classList.add('bg-blue-50');
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.currentTarget.classList.remove('bg-blue-50');
  };

  const handleDrop = (doc: SimbaDoc, e: React.DragEvent) => {
    e.preventDefault();
    e.currentTarget.classList.remove('bg-blue-50');
    if (draggedDocId && doc.metadata.is_folder) {
      handleMoveDocument(draggedDocId, doc.id);
    }
  };

  // When moving a document to a folder, update its folder_id
  const handleMoveDocument = (docId: string, targetFolderId: string | null) => {
    // Find the document in our list
    const doc = documents.find(d => d.id === docId);
    
    if (doc) {
      // In a real app, we'd update the backend here
      // For frontend-only, we'll store this association locally
      const updatedDoc = {
        ...doc,
        metadata: {
          ...doc.metadata,
          folder_id: targetFolderId
        }
      };
      
      // Update the document in the parent component
      onDocumentUpdate(updatedDoc);
      
      // Save the folder association to localStorage
      const associations = loadDocumentFolderAssociations();
      associations[docId] = targetFolderId;
      saveDocumentFolderAssociations(associations);
      
      toast({
        title: "Success",
        description: `Moved document to ${targetFolderId ? folders.find(f => f.id === targetFolderId)?.name : 'Home'}`
      });
    } else {
      toast({
        title: "Info",
        description: `Moved document to ${targetFolderId ? 'folder' : 'root'}`
      });
    }
  };

  // Use our local preview state
  const [previewDocument, setPreviewDocument] = useState<SimbaDoc | null>(null);
  
  // Handle preview click
  const handlePreview = (doc: SimbaDoc, e: React.MouseEvent) => {
    e.stopPropagation();
    setPreviewDocument(doc);
    // Call the provided onPreview 
    if (onPreview) {
      onPreview(doc);
    }
  };

  // Inside the DocumentList component, add state for parser config modal
  const [isParserConfigModalOpen, setIsParserConfigModalOpen] = useState(false);
  const [selectedDocumentForConfig, setSelectedDocumentForConfig] = useState<SimbaDoc | null>(null);

  // Add a function to handle opening the parser config modal
  const handleOpenParserConfig = (doc: SimbaDoc, e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    console.log("Opening parser config for document:", doc.id);
    
    // Set the document first
    setSelectedDocumentForConfig(doc);
    
    // Use setTimeout to ensure state updates have time to propagate
    setTimeout(() => {
      setIsParserConfigModalOpen(true);
      console.log("Parser config modal state set to true");
    }, 50);
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
            <Button
              variant="outline"
              size="sm"
              className="h-9"
              onClick={() => setShowCreateFolderDialog(true)}
            >
              <FolderPlus className="h-4 w-4 mr-2" />
              New Folder
            </Button>
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
              <TableCell colSpan={7}>
                <div className="flex items-center text-muted-foreground">
                  <div className="flex items-center gap-1">
                    {getBreadcrumbs().map((crumb, i, arr) => (
                      <React.Fragment key={crumb.id || 'root'}>
                        <button 
                          className={cn(
                            "hover:text-blue-500 text-xs px-1",
                            i === arr.length - 1 && "font-medium"
                          )}
                          onClick={() => setCurrentFolderId(crumb.id)}
                        >
                          {i === 0 ? <FolderOpen className="h-3 w-3 inline mr-1" /> : null}
                          {crumb.name}
                        </button>
                        {i < arr.length - 1 && <span className="text-gray-400">/</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </TableCell>
            </TableRow>
            
            {getCurrentFolderDocuments().map((doc, index) => (
              <TableRow 
                key={doc.id} 
                className={cn(
                  "hover:bg-gray-50",
                  doc.metadata.is_folder && "cursor-pointer"
                )}
                draggable={!doc.metadata.is_folder}
                onDragStart={(e) => {
                  if (!doc.metadata.is_folder) {
                    setDraggedDocId(doc.id);
                    e.dataTransfer.setData('text/plain', doc.id);
                  }
                }}
                onDragEnd={() => setDraggedDocId(null)}
                onDragOver={(e) => handleDragOver(doc, e)}
                onDragLeave={handleDragLeave}
                onDrop={(e) => handleDrop(doc, e)}
                onClick={() => {
                  if (doc.metadata.is_folder) {
                    handleFolderClick(doc.id);
                  }
                }}
              >
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
                    {isRenamingId === doc.id ? (
                      <Input
                        autoFocus
                        defaultValue={doc.metadata.filename}
                        className="h-8 w-[200px]"
                        onBlur={(e) => handleRenameDocument(doc.id, e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleRenameDocument(doc.id, e.currentTarget.value);
                          } else if (e.key === 'Escape') {
                            setIsRenamingId(null);
                          }
                        }}
                      />
                    ) : (
                      <div className="flex items-center gap-2">
                        <span 
                          className={cn("cursor-pointer", doc.metadata.is_folder && "font-medium hover:underline")}
                          onClick={() => {
                            if (doc.metadata.is_folder) {
                              handleFolderClick(doc.id);
                            }
                          }}
                        >
                          {doc.metadata.filename}
                        </span>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 opacity-0 group-hover:opacity-100"
                          onClick={(e) => {
                            e.stopPropagation();
                            setIsRenamingId(doc.id);
                          }}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
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
                    
                    {/* Show parser badge (without default label) */}
                    {doc.metadata.parser ? (
                      <div className="relative">
                        <Select
                          value={doc.metadata.parser || "docling"}
                          onValueChange={(value) => {
                            const updatedDoc = {
                              ...doc,
                              metadata: {
                                ...doc.metadata,
                                parser: value
                              }
                            };
                            onDocumentUpdate(updatedDoc);
                            toast({
                              title: "Parser Updated",
                              description: `Parser changed to ${value}`,
                            });
                          }}
                        >
                          <SelectTrigger 
                            className={cn(
                              "h-6 min-w-0 px-2.5 py-0 border rounded-md text-xs font-semibold gap-1 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:opacity-70",
                              doc.metadata.parser === 'docling' || !doc.metadata.parser
                                ? "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100" 
                                : "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100"
                            )}
                          >
                            <SelectValue>{doc.metadata.parser || "docling"}</SelectValue>
                          </SelectTrigger>
                          <SelectContent>
                            {availableParsers.map((parserName) => (
                              <SelectItem key={parserName} value={parserName}>
                                {parserName}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ) : (
                      <div className="relative">
                        <Select
                          value="docling"
                          onValueChange={(value) => {
                            const updatedDoc = {
                              ...doc,
                              metadata: {
                                ...doc.metadata,
                                parser: value
                              }
                            };
                            onDocumentUpdate(updatedDoc);
                            toast({
                              title: "Parser Set",
                              description: `Parser set to ${value}`,
                            });
                          }}
                        >
                          <SelectTrigger 
                            className="h-6 min-w-0 px-2.5 py-0 border rounded-md text-xs font-semibold bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 gap-1 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:opacity-70"
                          >
                            <SelectValue>docling</SelectValue>
                          </SelectTrigger>
                          <SelectContent>
                            {availableParsers.map((parserName) => (
                              <SelectItem key={parserName} value={parserName}>
                                {parserName}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    )}
                    
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
                  {doc.metadata.is_folder ? (
                    // For folders, show folder-specific actions
                    <div className="flex items-center justify-center gap-2">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={(e) => { 
                                e.stopPropagation(); 
                                setIsRenamingId(doc.id);
                              }}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Rename folder</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={(e) => handleDeleteFolder(doc.id, e)}
                              className="h-8 w-8 hover:bg-red-100 hover:text-red-600"
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Delete folder</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  ) : (
                    // For documents, show the existing document actions
                    <div className="flex items-center justify-center gap-2">
                      {/* Parse button */}
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
                            <p>Parse document</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      {/* Parser Config button */}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              id={`parser-config-button-${doc.id}`}
                              className="h-8 w-8 rounded-md hover:bg-gray-100 flex items-center justify-center"
                              onClick={(e) => handleOpenParserConfig(doc, e)}
                              type="button"
                            >
                              <Settings className="h-4 w-4" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>Configure parser</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      {/* View button */}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              id={`view-button-${doc.id}`}
                              variant="ghost"
                              size="icon"
                              onClick={(e) => handlePreview(doc, e)}
                              className="h-8 w-8"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>View document</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      {/* Delete button */}
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              id={`delete-button-${doc.id}`}
                              variant="ghost"
                              size="icon"
                              onClick={(e) => { e.stopPropagation(); onDelete(doc.id); }}
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
                  )}
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
                    enableDocument(doc, true);
                  });
                }}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Enable Selected
              </Button>
              <Button 
                size="lg"
                variant="outline"
                onClick={() => {
                  const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));
                  selectedDocs.forEach(doc => {
                    enableDocument(doc, false);
                  });
                }}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Disable Selected
              </Button>
            </div>
          </div>
        )}

        <Dialog open={showCreateFolderDialog} onOpenChange={setShowCreateFolderDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Folder</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <Input
                placeholder="Folder name"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateFolder();
                  }
                }}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateFolderDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateFolder}>
                Create
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <FileUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUpload={handleUpload}
          currentFolderId={currentFolderId}
          folderName={currentFolderId ? folders.find(f => f.id === currentFolderId)?.name : 'Home'}
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

        {/* Parser Configuration Modal */}
        <ParserConfigModal 
          isOpen={isParserConfigModalOpen}
          onClose={() => setIsParserConfigModalOpen(false)}
          document={selectedDocumentForConfig}
          onUpdate={(updatedDoc) => {
            console.log("Document updated with new parser:", updatedDoc.metadata.parser);
            onDocumentUpdate(updatedDoc);
            setSelectedDocumentForConfig(updatedDoc);
          }}
        />

      </CardContent>
    </div>
  );
};

export default DocumentList;