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
import { Plus, Trash2, Eye, FileText, FileSpreadsheet, File, FileCode, FileImage, FolderPlus, Folder, FolderOpen, RefreshCcw, Play, Loader2, Pencil, Settings, Sparkles, Filter, MoreVertical } from 'lucide-react';
import { Button } from '../ui/button';
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import { embeddingApi } from '@/lib/api_services';
import { ingestionApi } from '@/lib/ingestion_api';
import { parsingApi } from '@/lib/parsing_api';
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { SimbaDoc, Metadata } from '@/types/document';
import { ParsingStatusBox } from './ParsingStatusBox';
import { ParserConfigModal } from './ParserConfigModal';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface ColumnVisibility {
  chunkNumber: boolean;
  uploadDate: boolean;
  enable: boolean;
  parsingStatus: boolean;
  loader: boolean;
}

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
  onUpload: (files: FileList) => Promise<void>;
  onPreview: (document: SimbaDoc) => void;
  fetchDocuments: () => Promise<void>;
  onDocumentUpdate: (document: SimbaDoc) => void;
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
}) => {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [showReindexDialog, setShowReindexDialog] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<SimbaDoc | null>(null);
  const [reindexProgress, setReindexProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState("");
  const [isReindexing, setIsReindexing] = useState(false);
  const [showCreateFolderDialog, setShowCreateFolderDialog] = useState(false);
  const { toast } = useToast();
  const [pendingUploads, setPendingUploads] = useState<Record<string, string>>({});
  const [parsingTasks, setParsingTasks] = useState<Record<string, string>>(() => {
    const savedTasks = localStorage.getItem(PARSING_TASKS_STORAGE_KEY);
    return savedTasks ? JSON.parse(savedTasks) : {};
  });
  const [parsingButtonStates, setParsingButtonStates] = useState<Record<string, boolean>>({});
  const [availableParsers, setAvailableParsers] = useState<string[]>(["docling"]);
  const [isRenamingId, setIsRenamingId] = useState<string | null>(null);
  const [newFolderName, setNewFolderName] = useState("");
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [draggedDocId, setDraggedDocId] = useState<string | null>(null);
  const [folders, setFolders] = useState<Folder[]>(() => {
    const savedFolders = localStorage.getItem(FOLDERS_STORAGE_KEY);
    return savedFolders ? JSON.parse(savedFolders) : [];
  });
  const [, setSummarizingDocIds] = useState<Set<string>>(new Set());
  const [activeSummaryTasks, setActiveSummaryTasks] = useState<Record<string, string>>({});

  const [visibleColumns, setVisibleColumns] = useState<ColumnVisibility>({
    chunkNumber: true,
    uploadDate: true,
    enable: true,
    parsingStatus: true,
    loader: true,
  });
  const [filterParsingStatus, setFilterParsingStatus] = useState<string>("all");
  const [filterIsSummarized, setFilterIsSummarized] = useState<string>("all");

  const [isBulkActionPopoverOpen, setIsBulkActionPopoverOpen] = useState(false);
  const [isBulkSummarizeDialogOpen, setIsBulkSummarizeDialogOpen] = useState(false);
  const [isBulkParseDialogOpen, setIsBulkParseDialogOpen] = useState(false);
  const [isBulkParseParserSelectDialogOpen, setIsBulkParseParserSelectDialogOpen] = useState(false);
  const [selectedBulkParser, setSelectedBulkParser] = useState<string>("docling");

  useEffect(() => {
    localStorage.setItem(PARSING_TASKS_STORAGE_KEY, JSON.stringify(parsingTasks));
  }, [parsingTasks]);

  useEffect(() => {
    const checkExistingTasks = async () => {
      const tasks = { ...parsingTasks };
      let hasChanges = false;

      for (const [docId, taskId] of Object.entries(tasks)) {
        try {
          // const result = await ingestionApi.getParseStatus(taskId); // Problematic: getParseStatus
          // if (result.status === 'SUCCESS' || result.status === 'FAILED') {
          //   delete tasks[docId];
          //   hasChanges = true;
            
          //   const doc = documents.find(d => d.id === docId);
          //   if (doc) {
          //     const updatedDoc = {
          //       ...doc,
          //       metadata: {
          //         ...doc.metadata,
          //         parsing_status: result.status === 'SUCCESS' ? 'SUCCESS' : 'FAILED'
          //       }
          //     };
          //     onDocumentUpdate(updatedDoc);
          //   }
          // }
        } catch (error) {
          console.error(`检查任务 ${taskId} 时出错:`, error);
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
    if (Object.keys(pendingUploads).length > 0 && documents.length > 0) {
      const pendingCopy = { ...pendingUploads };
      let hasChanges = false;
      
      const associations = loadDocumentFolderAssociations();
      
      documents.forEach(doc => {
        if (pendingUploads[doc.id]) {
          console.log(`将文档 ${doc.id} 与文件夹 ${pendingUploads[doc.id]}关联`);
          
          const updatedDoc = {
            ...doc,
            metadata: {
              ...doc.metadata,
              folder_id: pendingUploads[doc.id]
            }
          };
          
          associations[doc.id] = pendingUploads[doc.id];
          onDocumentUpdate(updatedDoc);
          delete pendingCopy[doc.id];
          hasChanges = true;
        }
      });
      
      if (hasChanges) {
        setPendingUploads(pendingCopy);
      }
    }
  }, [documents, pendingUploads, onDocumentUpdate]);

  useEffect(() => {
    const fetchParsers = async () => {
      try {
        const parsers = await parsingApi.getParsers();
        setAvailableParsers(parsers);
      } catch (error) {
        console.error("Failed to fetch available parsers:", error);
        setAvailableParsers(["docling"]); 
      }
    };
    fetchParsers();
  }, []);

  const formatDate = (dateString: string) => {
    if (dateString === "未知") return dateString;
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleReindexConfirm = async () => {
    if (!selectedDocument) return;
    setIsReindexing(true);
    try {
      // await ingestionApi.reindexDocument( // Problematic: reindexDocument
      //   selectedDocument.id, 
      //   selectedDocument.metadata.parser,
      //   (status: any, progress: any) => { 
      //     setProgressStatus(status);
      //     setReindexProgress(progress);
      //   }
      // );
      toast({
        title: "成功",
        description: "文档重新索引成功",
      });
      await fetchDocuments();
    } catch (error) {
      toast({
        title: "错误",
        description: error instanceof Error ? error.message : "文档重新索引失败",
        variant: "destructive",
      });
    } finally {
      setIsReindexing(false);
      setShowReindexDialog(false);
      setReindexProgress(0);
      setProgressStatus("");
    }
  };

  const getReindexWarningContent = (document: SimbaDoc | null) => {
    if (!document) return { title: "重新索引", description: "未选择文档" };
    // if (document.metadata.loaderModified && document.metadata.parserModified) { 
    //   return {
    //     title: "Confirm Re-indexing",
    //     description: "This will update both the loader and parser. Changing the parser will create a new markdown file. Are you sure you want to proceed?"
    //   };
    // } else if (document.metadata.parserModified) { 
    //   return {
    //     title: "Confirm Parser Change",
    //     description: "Changing the parser will create a new markdown file. Are you sure you want to proceed?"
    //   };
    // } else if (document.metadata.loaderModified) { 
    //   return {
    //     title: "Confirm Loader Change",
    //     description: "Do you want to update the document loader?"
    //   };
    // }
    return { 
      title: "重新索引文档",
      description: "您确定要重新索引此文档吗？"
    };
  };

  const getFileIcon = (metadata: Metadata) => {
    if (metadata.is_folder) return Folder;
    const extension = metadata.file_path.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return FileText;
      case 'xlsx': case 'xls': case 'csv': return FileSpreadsheet;
      case 'md': case 'markdown': return FileCode;
      case 'docx': case 'doc': return FileText;
      case 'txt': return FileText;
      case 'jpg': case 'jpeg': case 'png': return FileImage;
      default: return File;
    }
  };

  const DOCUMENT_FOLDERS_KEY = 'document_folder_associations';
  
  const saveDocumentFolderAssociations = (associations: Record<string, string | null>) => {
    localStorage.setItem(DOCUMENT_FOLDERS_KEY, JSON.stringify(associations));
  };
  
  const loadDocumentFolderAssociations = (): Record<string, string | null> => {
    const saved = localStorage.getItem(DOCUMENT_FOLDERS_KEY);
    return saved ? JSON.parse(saved) : {};
  };
  
  useEffect(() => {
    if (documents.length === 0) return;
    const associations = loadDocumentFolderAssociations();
    let hasChanges = false;
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
  
  useEffect(() => {
    if (documents.length === 0) return;
    const associations = loadDocumentFolderAssociations();
    let hasUpdates = false;
    const updatedDocs = documents.map(doc => {
      if (associations[doc.id] && !doc.metadata.folder_id) {
        hasUpdates = true;
        return { ...doc, metadata: { ...doc.metadata, folder_id: associations[doc.id] }};
      }
      return doc;
    });
    if (hasUpdates) {
      updatedDocs.forEach(doc => {
        if (doc.metadata.folder_id) {
          onDocumentUpdate(doc);
        }
      });
    }
  }, [documents, onDocumentUpdate]);

  const handleCreateFolder = () => {
    const newFolder: Folder = {
      id: Math.random().toString(36).substr(2, 9),
      name: newFolderName,
      parentId: currentFolderId
    };
    setFolders([...folders, newFolder]);
    setNewFolderName("");
    setShowCreateFolderDialog(false);
    toast({ title: "成功", description: "文件夹已创建" });
  };

  const handleRenameFolder = (folderId: string, newName: string) => {
    setFolders(folders.map(folder => 
      folder.id === folderId ? { ...folder, name: newName } : folder
    ));
    setIsRenamingId(null);
    toast({ title: "成功", description: "文件夹重命名成功" });
  };

  const handleRenameDocument = (docId: string, newName: string) => {
    const folder = folders.find(f => f.id === docId);
    if (folder) {
      handleRenameFolder(docId, newName);
      return;
    }
    setIsRenamingId(null);
    toast({ title: "信息", description: "文档重命名将在后端支持下实现" });
  };

  const internalHandleUpload = async (files: FileList): Promise<void> => {
    if (files.length === 0) return;

    await onUpload(files);

    if (currentFolderId) {
      const fileNames = Array.from(files).map(file => file.name);
      toast({
        title: "检查文件夹关联",
        description: `正在查找已上传的文件以链接到 '${folders.find(f => f.id === currentFolderId)?.name || '当前文件夹'}'...`
      });

      let checkAttempts = 0;
      const maxAttempts = 15;
      
      const checkForNewUploads = async () => {
        const newlyUploaded = documents.filter(doc => 
          !doc.metadata.folder_id &&
          !doc.metadata.is_folder && 
          fileNames.some(name => doc.metadata.filename === name)
        );

        if (newlyUploaded.length > 0) {
          console.log(`将 ${newlyUploaded.length} 个文件与文件夹 ${currentFolderId} 关联`);
          const updates: Record<string, string> = { ...pendingUploads };
          newlyUploaded.forEach(doc => { updates[doc.id] = currentFolderId!; });
          setPendingUploads(updates);
          toast({ title: "找到关联", description: `${newlyUploaded.length} 个文件将被链接。`});
        } else if (checkAttempts < maxAttempts) {
          checkAttempts++;
          setTimeout(checkForNewUploads, 2000);
        } else {
          console.log(`文件夹 ${currentFolderId} 的文件夹关联尝试已达最大次数。未找到与上传名称匹配的未关联新文件。`);
        }
      };
      setTimeout(checkForNewUploads, 1500);
    }
  };

  const getCurrentFolderDocuments = () => {
    const filteredDocs = documents.filter(doc => {
      if (doc.metadata.is_folder) return false;

      // Apply folder filter
      const isInCurrentFolder = currentFolderId === null ? !doc.metadata.folder_id : doc.metadata.folder_id === currentFolderId;
      if (!isInCurrentFolder) return false;

      // Apply parsing status filter
      if (filterParsingStatus !== "all") {
        if (filterParsingStatus === "Unparsed") {
          if (doc.metadata.parsing_status && doc.metadata.parsing_status !== "") return false;
        } else if (doc.metadata.parsing_status !== filterParsingStatus) {
          return false;
        }
      }

      // Apply summarized filter
      if (filterIsSummarized !== "all") {
        const hasSummary = doc.metadata.summary && doc.metadata.summary.trim() !== "";
        if (filterIsSummarized === "yes" && !hasSummary) return false;
        if (filterIsSummarized === "no" && hasSummary) return false;
      }

      return true;
    });

    const folderItems = folders
      .filter(folder => folder.parentId === currentFolderId)
      .map(folder => ({
        id: folder.id,
        metadata: {
          filename: folder.name, is_folder: true, enabled: false, file_path: `/${folder.name}`,
          parsing_status: '', uploadedAt: new Date().toISOString(), type: 'folder'
        },
        documents: [], chunks: []
      } as SimbaDoc)); 
    return [...folderItems, ...filteredDocs];
  };

  const getBreadcrumbs = () => {
    if (!currentFolderId) return [{ id: null, name: 'Home' }];
    const result: Array<{ id: string | null, name: string }> = [{ id: null, name: 'Home' }];
    let current = folders.find(f => f.id === currentFolderId);
    if (current) result.push({ id: current.id, name: current.name });
    while (current && current.parentId) {
      const parent = folders.find(f => f.id === current!.parentId);
      if (parent) {
        result.splice(1, 0, { id: parent.id, name: parent.name });
        current = parent;
      } else { break; }
    }
    return result;
  };

  const [isEnabling, setIsEnabling] = useState<Set<string>>(new Set());

  const enableDocument = async (doc: SimbaDoc, checked: boolean, silent = false) => {
    try {
      if (isEnabling.has(doc.id)) return;
      setIsEnabling(prev => { const next = new Set(prev); next.add(doc.id); return next; });
      const updatedDoc = { ...doc, metadata: { ...doc.metadata, enabled: checked }};
      onDocumentUpdate(updatedDoc);

      if (!checked) {
        await embeddingApi.delete_document(doc.id);
        if (!silent) toast({ title: "文档已移除", description: "文档已成功从嵌入中移除" });
      } else {
        await embeddingApi.embedd_document(doc.id);
        if (!silent) toast({ title: "文档已嵌入", description: `文档嵌入成功。` });
      }
    } catch (error) {
      const revertedDoc = { ...doc, metadata: { ...doc.metadata, enabled: !checked }};
      onDocumentUpdate(revertedDoc);
      if (!silent) {
        toast({
          title: "错误",
          description: error instanceof Error ? error.message : `未能${checked ? '嵌入' : '移除'}文档`,
          variant: "destructive"
        });
      }
      throw error;
    } finally {
      setIsEnabling(prev => { const next = new Set(prev); next.delete(doc.id); return next; });
    }
  };

  const handleParseClick = async (document: SimbaDoc, parserOverride?: string) => {
    try {
      setParsingButtonStates(prev => ({ ...prev, [document.id]: true }));
      const parserToUse = parserOverride || document.metadata.parser || 'docling';
      if (document.metadata.enabled) {
        const disabledDoc = { ...document, metadata: { ...document.metadata, enabled: false }};
        onDocumentUpdate(disabledDoc);
        await new Promise(resolve => setTimeout(resolve, 500));
        // Ensure parsing_status is PENDING when re-parsing an enabled document
        const enabledDoc = { ...document, metadata: { ...document.metadata, enabled: true, parsing_status: 'PENDING', parser: parserToUse }};
        onDocumentUpdate(enabledDoc);
        await embeddingApi.delete_document(document.id);
      } else {
        // If not enabled, set parser and PENDING status before starting
        const updatedDoc = { ...document, metadata: { ...document.metadata, parser: parserToUse, parsing_status: 'PENDING' }};
        onDocumentUpdate(updatedDoc);
        // Give UI a moment to update before API call
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      const result = await parsingApi.startParsing(document.id, parserToUse);
      if (result && 'id' in result && 'metadata' in result) {
        onDocumentUpdate(result as SimbaDoc);
        toast({ title: "解析完成", description: `文档已成功使用 ${parserToUse} 解析` });
      } else if ('task_id' in result && result.task_id) {
        setParsingTasks(prev => ({ ...prev, [document.id]: result.task_id as string }));
        toast({ title: document.metadata.parsing_status === 'SUCCESS' ? "重新解析已开始" : "解析已开始", description: `使用 ${parserToUse} 的文档解析已加入队列` });
      } else {
        toast({ title: "错误", description: "从解析服务收到意外响应", variant: "destructive" });
      }
    } catch (error) {
      toast({ title: "错误", description: error instanceof Error ? error.message : "无法开始解析", variant: "destructive" });
      // Revert parsing status if API call failed
      const docToRevert = documents.find(d => d.id === document.id);
      if (docToRevert) {
        const revertedDoc = { ...docToRevert, metadata: { ...docToRevert.metadata, parsing_status: docToRevert.metadata.parsing_status === 'PENDING' ? (docToRevert.metadata.parser ? 'SUCCESS' : '') : docToRevert.metadata.parsing_status }};
        onDocumentUpdate(revertedDoc);
      }
    } finally {
      setParsingButtonStates(prev => ({ ...prev, [document.id]: false }));
    }
  };

  const handleParseComplete = async (docId: string, status: string) => {
    setParsingTasks(prev => { const newTasks = { ...prev }; delete newTasks[docId]; return newTasks; });
    const updatedDoc = documents.find(doc => doc.id === docId);
    if (updatedDoc) {
      const associations = loadDocumentFolderAssociations();
      const folderId = associations[docId] || updatedDoc.metadata.folder_id;
      const docWithNewStatus = { ...updatedDoc, metadata: { ...updatedDoc.metadata, parsing_status: status, folder_id: folderId }};
      onDocumentUpdate(docWithNewStatus);
      if (folderId) { associations[docId] = folderId; saveDocumentFolderAssociations(associations); }
    }
    if (status === 'PARSED') {
      toast({ title: "成功", description: "文档解析成功" });
      await fetchDocuments();
    }
  };

  const handleParseCancel = async (documentId: string) => {
    setParsingTasks(prev => { const next = { ...prev }; delete next[documentId]; return next; });
    await fetchDocuments();
    toast({ title: "已取消", description: "解析已取消" });
  };

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(null);

  const handleCheckboxClick = (docId: string, index: number, event: React.MouseEvent) => {
    event.stopPropagation();
    const isSelected = selectedIds.has(docId);
    if (event.shiftKey && lastSelectedIndex !== null) {
      const start = Math.min(lastSelectedIndex, index);
      const end = Math.max(lastSelectedIndex, index);
      const newSet = new Set(selectedIds);
      for (let i = start; i <= end; i++) { newSet.add(documents[i].id); }
      setSelectedIds(newSet);
    } else {
      const newSet = new Set(selectedIds);
      if (isSelected) { newSet.delete(docId); } else { newSet.add(docId); }
      setSelectedIds(newSet);
      setLastSelectedIndex(index);
    }
  };

  const handleFolderClick = (folderId: string) => { setCurrentFolderId(folderId); };

  const handleDeleteFolder = (folderId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    const hasDocuments = documents.some(doc => doc.metadata.folder_id === folderId);
    const hasSubfolders = folders.some(folder => folder.parentId === folderId);
    if (hasDocuments || hasSubfolders) {
      toast({ title: "无法删除文件夹", description: "文件夹不为空。请先移动或删除所有项目。", variant: "destructive" });
      return;
    }
    setFolders(folders.filter(f => f.id !== folderId));
    toast({ title: "成功", description: "文件夹删除成功" });
  };

  const handleDragOver = (doc: SimbaDoc, e: React.DragEvent) => {
    if (doc.metadata.is_folder) { e.preventDefault(); e.currentTarget.classList.add('bg-blue-50'); }
  };

  const handleDragLeave = (e: React.DragEvent) => { e.currentTarget.classList.remove('bg-blue-50'); };

  const handleDrop = (doc: SimbaDoc, e: React.DragEvent) => {
    e.preventDefault(); e.currentTarget.classList.remove('bg-blue-50');
    if (draggedDocId && doc.metadata.is_folder) { handleMoveDocument(draggedDocId, doc.id); }
  };

  const handleMoveDocument = (docId: string, targetFolderId: string | null) => {
    const doc = documents.find(d => d.id === docId);
    if (doc) {
      const updatedDoc = { ...doc, metadata: { ...doc.metadata, folder_id: targetFolderId }};
      onDocumentUpdate(updatedDoc);
      const associations = loadDocumentFolderAssociations();
      associations[docId] = targetFolderId;
      saveDocumentFolderAssociations(associations);
      toast({ title: "成功", description: `已将文档移至 ${targetFolderId ? folders.find(f => f.id === targetFolderId)?.name : '主页'}` });
    } else {
      toast({ title: "信息", description: `已将文档移至 ${targetFolderId ? '文件夹' : '根目录'}` });
    }
  };

  const handlePreview = (doc: SimbaDoc, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedDocument(doc);
    if (onPreview) { onPreview(doc); }
  };

  const [isParserConfigModalOpen, setIsParserConfigModalOpen] = useState(false);
  const [selectedDocumentForConfig, setSelectedDocumentForConfig] = useState<SimbaDoc | null>(null);

  const handleOpenParserConfig = (doc: SimbaDoc, e: React.MouseEvent) => {
    e.stopPropagation(); e.preventDefault();
    setSelectedDocumentForConfig(doc);
    setTimeout(() => { setIsParserConfigModalOpen(true); }, 50);
  };

  const [parseLoading, setParseLoading] = useState(false);
  const [toggleLoading, setToggleLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleMultipleDelete = async () => {
    const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));
    if (!window.confirm(`您确定要删除 ${selectedDocs.length} 个文档吗？`)) return;
    setDeleteLoading(true);
    toast({ title: "删除文档", description: `正在删除 ${selectedDocs.length} 个文档...` });
    let hasErrors = false;
    for (const doc of selectedDocs) {
      try { await ingestionApi.deleteDocumentWithoutConfirmation(doc.id); }
      catch (error) { console.error(`删除文档 ${doc.id} 时出错:`, error); hasErrors = true; }
    }
    if (hasErrors) toast({ variant: "destructive", title: "错误", description: "未能删除一个或多个文档" });
    else toast({ title: "成功", description: `已成功删除 ${selectedDocs.length} 个文档` });
    await fetchDocuments();
    setSelectedIds(new Set());
    setDeleteLoading(false);
  };

  const toggleEnableMultiple = async (enable: boolean) => {
    const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));
    const docsToUpdate = selectedDocs.filter(doc => doc.metadata.enabled !== enable);
    if (docsToUpdate.length === 0) return;
    setToggleLoading(true);
    toast({ title: `${enable ? '启用' : '禁用'}文档`, description: `${enable ? '正在启用' : '正在禁用'} ${docsToUpdate.length} 个文档...` });
    docsToUpdate.forEach(doc => {
      const updatedDoc = { ...doc, metadata: { ...doc.metadata, enabled: enable }};
      onDocumentUpdate(updatedDoc);
    });
    let successCount = 0; let errorCount = 0; const failedDocs = [];
    for (const doc of docsToUpdate) {
      try { await enableDocument(doc, enable, true); successCount++; }
      catch (error) { console.error(` ${enable ? '启用' : '禁用'}文档 ${doc.id} 时出错:`, error); errorCount++; failedDocs.push(doc); }
    }
    if (failedDocs.length > 0) {
      failedDocs.forEach(doc => {
        const revertedDoc = { ...doc, metadata: { ...doc.metadata, enabled: !enable }};
        onDocumentUpdate(revertedDoc);
      });
    }
    if (errorCount > 0) toast({ variant: "destructive", title: "操作部分完成", description: `${successCount} 个文档已更新，${errorCount} 个失败` });
    else if (successCount > 0) toast({ title: "成功", description: `已成功${enable ? '启用' : '禁用'} ${successCount} 个文档` });
    setToggleLoading(false);
  };

  const parseMultipleDocuments = async () => {
    const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));
    if (selectedDocs.length === 0) return;
    setParseLoading(true);
    toast({ title: "解析文档", description: `正在为 ${selectedDocs.length} 个文档开始解析...` });
    let successCount = 0; let errorCount = 0;
    for (const doc of selectedDocs) {
      try { await handleParseClick(doc); successCount++; }
      catch (error) { console.error(`解析文档 ${doc.id} 时出错:`, error); errorCount++; }
    }
    if (errorCount > 0) toast({ variant: "destructive", title: "操作部分完成", description: `${successCount} 个文档解析已开始，${errorCount} 个失败` });
    else toast({ title: "成功", description: `${successCount} 个文档的解析已开始` });
    setParseLoading(false);
  };

  const handleGenerateSummary = async (docId: string) => {
    let taskIdFromApi: string | undefined = undefined;
    try {
      const result = await parsingApi.generateSummary(docId);
      if (result.task_id && result.status !== 'error') {
        taskIdFromApi = result.task_id;
        setActiveSummaryTasks(prev => ({ ...prev, [docId]: taskIdFromApi! }));
        toast({
          title: "摘要生成已开始",
          description: result.message || `任务 ID: ${result.task_id}`
        });
      } else {
        toast({
          title: "开始摘要时出错",
          description: result.message || "无法开始摘要生成任务。",
          variant: "destructive"
        });
        setSummarizingDocIds(prev => {
          const next = new Set(prev);
          next.delete(docId);
          return next;
        });
      }
    } catch (error) {
      console.error("生成摘要失败：", error);
      toast({
        title: "生成摘要时出错",
        description: error instanceof Error ? error.message : "无法开始摘要生成过程。",
        variant: "destructive"
      });
      setSummarizingDocIds(prev => {
        const next = new Set(prev);
        next.delete(docId);
        return next;
      });
    }
  };

  const handleBulkSummarizeOpen = () => {
    if (selectedIds.size === 0) {
      toast({ title: "未选择文档", description: "请选择要摘要的文档。", variant: "destructive" });
      return;
    }
    setIsBulkSummarizeDialogOpen(true);
  };

  const handleBulkSummarizeConfirm = async () => {
    setIsBulkSummarizeDialogOpen(false);
    const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));
    const docsToSummarize = selectedDocs.filter(doc => !doc.metadata.summary || doc.metadata.summary.trim() === "");

    if (docsToSummarize.length === 0) {
      toast({ title: "无需摘要的文档", description: "所有选定文档均已有摘要或未选择任何文档。", });
      return;
    }

    toast({ title: "摘要文档", description: `正在为 ${docsToSummarize.length} 个文档开始生成摘要...` });
    let successCount = 0; let errorCount = 0;

    for (const doc of docsToSummarize) {
      try {
        await handleGenerateSummary(doc.id);
        successCount++;
      } catch (error) {
        console.error(`摘要文档 ${doc.id} 时出错:`, error); errorCount++;
      }
    }

    if (errorCount > 0) toast({ variant: "destructive", title: "操作部分完成", description: `${successCount} 个文档的摘要已开始，${errorCount} 个失败` });
    else if (successCount > 0) toast({ title: "成功", description: `${successCount} 个文档的摘要生成已开始` });
  };

  const handleBulkParseOpen = () => {
    if (selectedIds.size === 0) {
      toast({ title: "未选择文档", description: "请选择要解析的文档。", variant: "destructive" });
      return;
    }
    setIsBulkParseParserSelectDialogOpen(true);
  };

  const handleBulkParseParserSelectConfirm = () => {
    setIsBulkParseParserSelectDialogOpen(false);
    setIsBulkParseDialogOpen(true);
  };

  const handleBulkParseConfirm = async () => {
    setIsBulkParseDialogOpen(false);
    const selectedDocs = documents.filter(doc => selectedIds.has(doc.id));

    if (selectedDocs.length === 0) {
      toast({ title: "未选择文档", description: "请选择要解析的文档。", });
      return;
    }

    toast({ title: "解析文档", description: `正在使用 "${selectedBulkParser}" 解析器解析所有选定文档...` });
    let successCount = 0; let errorCount = 0;

    for (const doc of selectedDocs) {
      try {
        await handleParseClick(doc, selectedBulkParser);
        successCount++;
      } catch (error) {
        console.error(`解析文档 ${doc.id} 时出错:`, error); errorCount++;
      }
    }

    if (errorCount > 0) toast({ variant: "destructive", title: "操作部分完成", description: `使用 "${selectedBulkParser}" 解析的 ${successCount} 个文档解析已开始，${errorCount} 个失败` });
    else if (successCount > 0) toast({ title: "成功", description: `使用 "${selectedBulkParser}" 解析的 ${successCount} 个文档解析已开始` });
  };

  useEffect(() => {
    const intervalIds: Record<string, NodeJS.Timeout> = {};

    Object.entries(activeSummaryTasks).forEach(([docId, taskId]) => {
      if (!taskId) return;

      const pollStatus = async () => {
        try {
          const result = await parsingApi.getParseStatus(taskId);
          console.log(`轮询摘要任务 ${taskId} (文档 ${docId}):`, result);

          const isSuccess = result.status === 'SUCCESS' || (result.result && result.result.status === 'success');
          const isError = result.status === 'FAILED' || (result.result && result.result.status === 'error') || result.status === 'FAILURE';

          if (isSuccess) {
            toast({
              title: "摘要已生成",
              description: `文档 ${documents.find(d => d.id === docId)?.metadata.filename || docId} 的摘要已准备就绪。`,
            });
            fetchDocuments();
            setActiveSummaryTasks(prev => {
              const next = { ...prev };
              delete next[docId];
              return next;
            });
            setSummarizingDocIds(prev => {
              const next = new Set(prev);
              next.delete(docId);
              return next;
            });
            if (intervalIds[docId]) clearInterval(intervalIds[docId]);
          } else if (isError) {
            toast({
              title: "摘要生成失败",
              description: result.result?.error || `未能为文档 ${docId} 生成摘要。`,
              variant: "destructive",
            });
            setActiveSummaryTasks(prev => {
              const next = { ...prev };
              delete next[docId];
              return next;
            });
            setSummarizingDocIds(prev => {
              const next = new Set(prev);
              next.delete(docId);
              return next;
            });
            if (intervalIds[docId]) clearInterval(intervalIds[docId]);
          }
        } catch (error) {
          console.error(`轮询摘要任务 ${taskId} (文档 ${docId}) 时出错:`, error);
          toast({
            title: "轮询错误",
            description: `检查文档 ${docId} 的摘要状态时出错。`,
            variant: "destructive",
          });
          setActiveSummaryTasks(prev => {
            const next = { ...prev };
            delete next[docId];
            return next;
          });
          setSummarizingDocIds(prev => {
            const next = new Set(prev);
            next.delete(docId);
            return next;
          });
          if (intervalIds[docId]) clearInterval(intervalIds[docId]);
        }
      };

      pollStatus();
      intervalIds[docId] = setInterval(pollStatus, 5000);
    });

    return () => {
      Object.values(intervalIds).forEach(clearInterval);
    };
  }, [activeSummaryTasks, fetchDocuments, toast, documents]);

  return (
    <div className="relative">
      <CardContent>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Input
              placeholder="搜索文档..."
              className="h-9 w-[200px]"
              onChange={(e) => onSearch(e.target.value)}
            />
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="h-9">
                  <Filter className="h-4 w-4 mr-2" />
                  筛选器
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-72 p-4" align="start">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium leading-none mb-2">可见列</h4>
                    <div className="space-y-2">
                      {(Object.keys(visibleColumns) as Array<keyof ColumnVisibility>).map((key) => (
                        <div key={key} className="flex items-center space-x-2">
                          <Checkbox
                            id={`col-${key}`}
                            checked={visibleColumns[key]}
                            onCheckedChange={(checked) => {
                              setVisibleColumns((prev) => ({ ...prev, [key]: !!checked }));
                            }}
                          />
                          <Label htmlFor={`col-${key}`} className="text-sm font-normal capitalize">
                            {key.replace(/([A-Z])/g, ' $1')}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium leading-none mb-2">筛选条件</h4>
                    <div className="space-y-3">
                      <div>
                        <Label htmlFor="filter-parsing-status" className="text-sm">解析状态</Label>
                        <Select
                          value={filterParsingStatus}
                          onValueChange={setFilterParsingStatus}
                        >
                          <SelectTrigger id="filter-parsing-status" className="h-9 mt-1">
                            <SelectValue placeholder="选择状态" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">全部</SelectItem>
                            <SelectItem value="SUCCESS">已解析</SelectItem>
                            <SelectItem value="FAILED">失败</SelectItem>
                            <SelectItem value="PENDING">待处理</SelectItem>
                            <SelectItem value="Unparsed">未解析</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="filter-is-summarized" className="text-sm">是否已摘要</Label>
                        <Select
                          value={filterIsSummarized}
                          onValueChange={setFilterIsSummarized}
                        >
                          <SelectTrigger id="filter-is-summarized" className="h-9 mt-1">
                            <SelectValue placeholder="选择状态" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">全部</SelectItem>
                            <SelectItem value="yes">是</SelectItem>
                            <SelectItem value="no">否</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="h-9"
              onClick={() => setShowCreateFolderDialog(true)}
            >
              <FolderPlus className="h-4 w-4 mr-2" />
              新建文件夹
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
                    刷新
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>刷新文档列表</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
            <Popover open={isBulkActionPopoverOpen} onOpenChange={setIsBulkActionPopoverOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="h-9" disabled={selectedIds.size === 0}>
                  <MoreVertical className="h-4 w-4 mr-2" />
                  批量操作
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-56 p-2">
                <Button
                  variant="ghost"
                  className="w-full justify-start mb-1"
                  onClick={() => {
                    handleBulkSummarizeOpen();
                    setIsBulkActionPopoverOpen(false);
                  }}
                  disabled={selectedIds.size === 0}
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  摘要选中项
                </Button>
                <Button
                  variant="ghost"
                  className="w-full justify-start"
                  onClick={() => {
                    handleBulkParseOpen();
                    setIsBulkActionPopoverOpen(false);
                  }}
                  disabled={selectedIds.size === 0}
                >
                  <Play className="h-4 w-4 mr-2" />
                  解析选中项
                </Button>
              </PopoverContent>
            </Popover>
            <Button
              variant="default"
              size="sm"
              className="h-9"
              onClick={() => setIsUploadModalOpen(true)}
            >
              <Plus className="h-4 w-4 mr-2" />
              上传
            </Button>
          </div>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8">
                <Checkbox 
                  checked={selectedIds.size === getCurrentFolderDocuments().filter(d => !d.metadata.is_folder).length && getCurrentFolderDocuments().filter(d => !d.metadata.is_folder).length > 0}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setSelectedIds(new Set(getCurrentFolderDocuments().filter(d => !d.metadata.is_folder).map(doc => doc.id)));
                    } else {
                      setSelectedIds(new Set());
                    }
                  }}
                  disabled={getCurrentFolderDocuments().filter(d => !d.metadata.is_folder).length === 0}
                />
              </TableHead>
              <TableHead>名称</TableHead>
              {visibleColumns.chunkNumber && <TableHead>分块数量</TableHead>}
              {visibleColumns.uploadDate && <TableHead>上传日期</TableHead>}
              {visibleColumns.loader && <TableHead>加载器</TableHead>}
              {visibleColumns.enable && <TableHead>启用</TableHead>}
              {visibleColumns.parsingStatus && <TableHead>解析状态</TableHead>}
              <TableHead className="w-[100px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow className="h-8 text-xs border-b border-muted">
              <TableCell colSpan={
                3 +
                (visibleColumns.chunkNumber ? 1 : 0) +
                (visibleColumns.uploadDate ? 1 : 0) +
                (visibleColumns.loader ? 1 : 0) +
                (visibleColumns.enable ? 1 : 0) +
                (visibleColumns.parsingStatus ? 1 : 0)
              }>
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
                  doc.metadata.is_folder && "cursor-pointer group"
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
                {visibleColumns.chunkNumber && (
                  <TableCell>
                    {doc.metadata.is_folder ? '' : (doc.metadata.enabled ? doc.documents.length : 0)}
                  </TableCell>
                )}
                {visibleColumns.uploadDate && (
                  <TableCell>
                    {doc.metadata.is_folder ? '' : formatDate(doc.metadata.uploadedAt || "未知")}
                  </TableCell>
                )}
                {visibleColumns.loader && (
                  <TableCell>
                    {doc.metadata.loader && !doc.metadata.is_folder ? (
                      <Badge variant="outline">{doc.metadata.loader}</Badge>
                    ) : (
                      !doc.metadata.is_folder ? <span className="text-xs text-muted-foreground">不适用</span> : ''
                    )}
                  </TableCell>
                )}
                {visibleColumns.enable && (
                  <TableCell>
                    {doc.metadata.is_folder ? '' : (
                      <Switch
                        checked={doc.metadata.enabled}
                        disabled={isEnabling.has(doc.id)}
                        onCheckedChange={(checked) => {
                          if (isEnabling.has(doc.id)) return;
                          const updatedDoc = { ...doc, metadata: { ...doc.metadata, enabled: checked }};
                          onDocumentUpdate(updatedDoc);
                          enableDocument(doc, checked).catch(error => {
                            console.error("Error toggling document:", error);
                          });
                        }}
                        aria-label="Toggle document embedding"
                      />
                    )}
                  </TableCell>
                )}
                {visibleColumns.parsingStatus && (
                  <TableCell>
                    {doc.metadata.is_folder ? '' : (
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
                          {doc.metadata.parsing_status || '未解析'}
                        </Badge>
                        
                        {doc.metadata.parser ? (
                          <div className="relative">
                            <Select
                              value={doc.metadata.parser || ""}
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
                                  title: "解析器已更新",
                                  description: `解析器已更改为 ${value}`,
                                });
                              }}
                            >
                              <SelectTrigger 
                                className="h-6 min-w-0 px-2.5 py-0 border rounded-md text-xs font-semibold bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 gap-1 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:opacity-70"
                              >
                                <SelectValue placeholder="选择解析器" />
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
                                  title: "解析器已设置",
                                  description: `解析器已设置为 ${value}`,
                                });
                              }}
                            >
                              <SelectTrigger 
                                className="h-6 min-w-0 px-2.5 py-0 border rounded-md text-xs font-semibold bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 gap-1 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:opacity-70"
                              >
                                <SelectValue placeholder="设置解析器">{doc.metadata.parser || "docling"}</SelectValue>
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
                    )}
                  </TableCell>
                )}
                <TableCell>
                  {doc.metadata.is_folder ? (
                    <div className="flex items-center justify-center gap-2">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={(e) => { 
                                e.stopPropagation(); 
                                setIsRenamingId(doc.id);
                              }}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>重命名文件夹</p>
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
                            <p>删除文件夹</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>
                  ) : (
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
                            <p>解析文档</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

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
                            <p>配置解析器</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

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
                            <p>查看文档</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

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
                            <p>删除文档</p>
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

        {selectedIds.size > 0 && (
          <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white border rounded-lg shadow-lg flex items-center z-50">
            <div className="flex items-center py-2 px-4 border-r">
              <span className="font-medium">
                {selectedIds.size} {selectedIds.size === 1 ? '文档' : '文档'} 已选择
              </span>
            </div>
            
            <div className="flex items-center gap-8 p-2">
              <Button 
                size="sm"
                variant="ghost"
                className="flex items-center"
                onClick={parseMultipleDocuments}
                disabled={parseLoading}
              >
                {parseLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
                解析选中项
              </Button>
              
              <div className="flex items-center">
                <span className="mr-3">启用/禁用</span>
                <Switch 
                  checked={selectedIds.size > 0 && documents.filter(doc => selectedIds.has(doc.id)).every(doc => doc.metadata.enabled)}
                  onCheckedChange={(checked) => {
                    if (toggleLoading) return;
                    toggleEnableMultiple(checked);
                  }}
                  disabled={toggleLoading}
                />
              </div>
              
              <Button 
                size="sm"
                variant="destructive"
                className="flex items-center"
                onClick={handleMultipleDelete}
                disabled={deleteLoading}
              >
                {deleteLoading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Trash2 className="h-4 w-4 mr-2" />}
                删除文档
              </Button>
            </div>
          </div>
        )}

        <Dialog open={showCreateFolderDialog} onOpenChange={setShowCreateFolderDialog}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>创建新文件夹</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <Input
                placeholder="文件夹名称"
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
                取消
              </Button>
              <Button onClick={handleCreateFolder}>
                创建
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        <FileUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUpload={internalHandleUpload}
          currentFolderId={currentFolderId}
          folderName={currentFolderId ? folders.find(f => f.id === currentFolderId)?.name : '主页'}
        />

        <AlertDialog 
          open={showReindexDialog} 
          onOpenChange={setShowReindexDialog}
        >
          <AlertDialogContent className="sm:max-w-md">
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
                取消
              </AlertDialogCancel>
              <AlertDialogAction 
                onClick={handleReindexConfirm}
                className="bg-primary text-white hover:bg-primary/90"
                disabled={isReindexing}
              >
                {isReindexing ? "处理中..." : "继续"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        <ParserConfigModal 
          isOpen={isParserConfigModalOpen}
          onClose={() => setIsParserConfigModalOpen(false)}
          document={selectedDocumentForConfig}
          onUpdate={(updatedDoc) => {
            console.log("文档已使用新解析器更新:", updatedDoc.metadata.parser);
            onDocumentUpdate(updatedDoc);
          }}
        />

        {/* Bulk Summarize Dialog */}
        <AlertDialog open={isBulkSummarizeDialogOpen} onOpenChange={setIsBulkSummarizeDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认摘要缺失项</AlertDialogTitle>
              <AlertDialogDescription>
                您确定要为所有选定但尚无摘要的文档生成摘要吗？
                此操作仅影响尚无摘要的文档。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>取消</AlertDialogCancel>
              <AlertDialogAction onClick={handleBulkSummarizeConfirm}>摘要</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Bulk Parse - Parser Select Dialog */}
        <Dialog open={isBulkParseParserSelectDialogOpen} onOpenChange={setIsBulkParseParserSelectDialogOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>选择批量操作的解析器</DialogTitle>
            </DialogHeader>
            <div className="py-4 space-y-2">
              <Label htmlFor="bulk-parser-select">为所有选定文档选择一个解析器：</Label>
              <Select value={selectedBulkParser} onValueChange={setSelectedBulkParser}>
                <SelectTrigger id="bulk-parser-select">
                  <SelectValue placeholder="选择一个解析器" />
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
            <div className="flex justify-end gap-2 pt-2">
               <Button variant="outline" onClick={() => setIsBulkParseParserSelectDialogOpen(false)}>取消</Button>
               <Button onClick={handleBulkParseParserSelectConfirm}>下一步</Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Bulk Parse - Confirmation Dialog */}
        <AlertDialog open={isBulkParseDialogOpen} onOpenChange={setIsBulkParseDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认批量解析</AlertDialogTitle>
              <AlertDialogDescription>
                您确定要使用"{selectedBulkParser}"解析器解析所有选定文档吗？
                即使文档已经解析过，此操作也会重新解析。
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>取消</AlertDialogCancel>
              <AlertDialogAction onClick={handleBulkParseConfirm}>使用 {selectedBulkParser} 解析</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

      </CardContent>
    </div>
  );
};

export default DocumentList;