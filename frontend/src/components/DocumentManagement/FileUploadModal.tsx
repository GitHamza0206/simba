import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { useState, useRef } from "react"
import { Upload, Trash2, FolderUp } from "lucide-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
// import { toast } from "@/components/ui/use-toast" // Removed unused import
// import { ingestionApi } from "@/lib/ingestion_api" // Commenting out direct API call

interface FileUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUpload: (files: FileList) => Promise<void>; // Added onUpload prop
  currentFolderId?: string | null
  folderName?: string
}

export function FileUploadModal({ 
  isOpen, 
  onClose, 
  onUpload, // Destructure onUpload
  currentFolderId = null, 
  folderName = 'Home' 
}: FileUploadModalProps) {
  const [dragActive, setDragActive] = useState(false)
  const [activeTab, setActiveTab] = useState("file")
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null)
  const [destinationPath, setDestinationPath] = useState("/")
  const [recursive, setRecursive] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const directoryInputRef = useRef<HTMLInputElement>(null)

  const addFiles = (newFiles: FileList) => {
    setSelectedFiles(prevFiles => {
      const dt = new DataTransfer();
      
      // Add existing files
      if (prevFiles) {
        Array.from(prevFiles).forEach(file => {
          dt.items.add(file);
        });
      }
      
      // Add new files
      Array.from(newFiles).forEach(file => {
        dt.items.add(file);
      });
      
      return dt.files;
    });
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      addFiles(e.dataTransfer.files)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      addFiles(e.target.files)
    }
  }

  const handleDirectorySelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(e.target.files); // treat as files to upload
    }
  }

  const removeFile = (indexToRemove: number) => {
    if (!selectedFiles) return;
    
    const dt = new DataTransfer();
    Array.from(selectedFiles).forEach((file, index) => {
      if (index !== indexToRemove) {
        dt.items.add(file);
      }
    });
    setSelectedFiles(dt.files);
  };

  const handleUpload = async () => {
    if (selectedFiles && selectedFiles.length > 0) {
      try {
        setIsUploading(true);
        // await ingestionApi.uploadDocuments(Array.from(selectedFiles)); // Replaced with onUpload call
        await onUpload(selectedFiles); // Call the passed onUpload function
        
        // Toasting and onClose will now be handled by the parent (DocumentList) 
        // to ensure correct feedback after all parent logic (like fetchDocuments) is done.
        // toast({
        //   title: "Success",
        //   description: `Files uploaded successfully!`,
        // });
        // onClose(); // Parent will call onClose after its handleUpload completes
      } catch (error) {
        console.error('Error during upload process:', error); // Log error from parent
        // Parent (DocumentList) will show its own error toast
        // toast({
        //   title: "Error",
        //   description: "Failed to upload files. Please try again.",
        //   variant: "destructive"
        // });
      } finally {
        setIsUploading(false);
      }
    }
  }

  const handleAreaClick = () => {
    if (activeTab === "file") {
      fileInputRef.current?.click()
    } else {
      directoryInputRef.current?.click()
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{activeTab === "file" ? "上传文件" : "上传文件夹"}{currentFolderId ? `到${folderName}` : ''}</DialogTitle>
          <DialogDescription>
            选择要上传到您的文档集合的文件或文件夹。
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="file">文件上传</TabsTrigger>
            <TabsTrigger value="directory">文件夹上传</TabsTrigger>
          </TabsList>

          <TabsContent value="file" className="flex-1 flex flex-col min-h-0">
            <div className="mt-4 space-y-4 flex-1 flex flex-col">
              {currentFolderId && (
                <div className="text-sm text-blue-600 mb-2 flex items-center">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                  </svg>
                  上传到：{folderName}
                </div>
              )}
              
              <div
                className={`grid place-items-center border-2 border-dashed rounded-lg h-32 flex-shrink-0 ${
                  dragActive ? "border-primary" : "border-gray-300"
                } cursor-pointer`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={handleAreaClick}
              >
                <div className="text-center">
                  <Upload className="w-10 h-10 mx-auto text-blue-500 mb-2" />
                  <p className="text-sm text-gray-600">
                    点击或拖拽文件到此区域上传
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    支持单个或批量上传。严禁上传公司数据或其他受限文件。
                  </p>
                </div>
              </div>

              {selectedFiles && selectedFiles.length > 0 && (
                <div className="border rounded-lg shadow-sm">
                  <div className="max-h-[200px] overflow-y-auto p-2">
                    <div className="space-y-1">
                      {Array.from(selectedFiles).map((file, index) => (
                        <div 
                          key={index} 
                          className="flex items-center justify-between text-sm text-gray-600 py-1 px-2 rounded-md hover:bg-gray-100 group"
                        >
                          <div className="flex items-center gap-2 min-w-0 flex-1">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500 flex-shrink-0">
                              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                            </svg>
                            <span className="truncate">{file.name}</span>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              removeFile(index);
                            }}
                          >
                            <Trash2 className="h-4 w-4 text-gray-500" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="directory" className="flex-1">
            <div className="mt-4 space-y-4">
              <div
                className={`grid place-items-center border-2 border-dashed rounded-lg h-32 flex-shrink-0 ${
                  dragActive ? "border-primary" : "border-gray-300"
                } cursor-pointer`}
                onClick={handleAreaClick}
              >
                <div className="text-center">
                  <FolderUp className="w-10 h-10 mx-auto text-blue-500 mb-2" />
                  <p className="text-sm text-gray-600">
                    Click to select folders to upload
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    Select one or more folders to be processed for ingestion
                  </p>
                </div>
              </div>

              <div className="space-y-3 mt-4">
                <div className="flex flex-col space-y-1.5">
                  <Label htmlFor="destination-path">Destination Path</Label>
                  <Input
                    id="destination-path"
                    value={destinationPath}
                    onChange={(e) => setDestinationPath(e.target.value)}
                    placeholder="Destination path (e.g., /my-documents)"
                  />
                  <p className="text-xs text-gray-500">Where to store the ingested documents</p>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="recursive" 
                    checked={recursive} 
                    onCheckedChange={(checked) => setRecursive(checked as boolean)} 
                  />
                  <Label htmlFor="recursive">Process subfolders recursively</Label>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter className="flex justify-between mt-6">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <div>
            <Input
              ref={fileInputRef}
              id="file-upload"
              type="file"
              multiple
              className="hidden"
              onChange={handleChange}
              accept=".pdf,.doc,.docx,.txt,.md"
            />
            <input
              ref={directoryInputRef}
              id="directory-upload"
              type="file"
              // @ts-expect-error - webkitdirectory and directory are valid attributes but not in TypeScript definitions
              webkitdirectory=""
              directory=""
              multiple
              className="hidden"
              onChange={handleDirectorySelect}
            />
            <Button 
              onClick={handleUpload}
              disabled={(activeTab === "file" && !selectedFiles) || 
                        (activeTab === "directory" && !selectedFiles) ||
                        isUploading}
            >
              {isUploading ? "Uploading..." : "OK"}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
} 