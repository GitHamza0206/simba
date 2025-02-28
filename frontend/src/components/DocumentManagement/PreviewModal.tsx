import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import ReactMarkdown from 'react-markdown';
import { useState, useEffect, useRef } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Pencil, Check, Trash2, Wand2, Download, ExternalLink, RefreshCw, AlertTriangle, Maximize } from 'lucide-react';
import { ingestionApi, previewApi } from "@/lib/api_services";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from '@/lib/utils';

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: SimbaDoc | null;
  onUpdate: (document: SimbaDoc) => void;
}

const PreviewModal: React.FC<PreviewModalProps> = ({ 
  isOpen, 
  onClose, 
  document,
  onUpdate
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(true);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [renderFailed, setRenderFailed] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [isFullyClosed, setIsFullyClosed] = useState(!isOpen);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isEditingLoader, setIsEditingLoader] = useState(false);
  const [isEditingParser, setIsEditingParser] = useState(false);
  const [selectedLoader, setSelectedLoader] = useState(document?.metadata.loader);
  const [confirmedLoader, setConfirmedLoader] = useState(document?.metadata.loader);
  const [selectedParser, setSelectedParser] = useState(document?.metadata.parser);
  const [confirmedParser, setConfirmedParser] = useState(document?.metadata.parser);
  const [loaders, setLoaders] = useState<string[]>([]);
  const [parsers, setParsers] = useState<string[]>([]);

  // Track when modal is fully closed
  useEffect(() => {
    if (!isOpen) {
      // Set a slight delay to ensure animations complete
      const timer = setTimeout(() => {
        setIsFullyClosed(true);
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setIsFullyClosed(false);
    }
  }, [isOpen]);

  // Clean up resources when component unmounts
  useEffect(() => {
    return () => {
      if (iframeRef.current) {
        // Clear iframe src to stop any ongoing loading
        try {
          if (iframeRef.current.contentWindow) {
            iframeRef.current.src = 'about:blank';
          }
        } catch (e) {
          console.log('Failed to clean iframe:', e);
        }
      }
    };
  }, []);

  // Add a timeout to hide the loading spinner after 5 seconds
  // This is a fallback in case the onLoad event doesn't fire properly
  useEffect(() => {
    if (previewLoading && document) {
      const timer = setTimeout(() => {
        console.log('Loading timeout reached, hiding spinner');
        setPreviewLoading(false);
      }, 5000); // 5 seconds
      
      return () => clearTimeout(timer);
    }
  }, [previewLoading, document, retryCount]);

  useEffect(() => {
    if (document) {
      setPreviewLoading(true);
      setPreviewError(null);
      setRenderFailed(false);
    }
  }, [document]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [loadersResponse, parsersResponse] = await Promise.all([
          ingestionApi.getLoaders(),
          ingestionApi.getParsers()
        ]);
        setLoaders(loadersResponse);
        setParsers(parsersResponse);
      } catch (error) {
        console.error('Error fetching loaders and parsers:', error);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    setSelectedLoader(document?.metadata.loader);
    setConfirmedLoader(document?.metadata.loader);
    setSelectedParser(document?.metadata.parser);
    setConfirmedParser(document?.metadata.parser);
  }, [document]);

  const handleLoaderChange = (value: string) => {
    setSelectedLoader(value);
  };

  const handleParserChange = (value: string) => {
    setSelectedParser(value);
  };

  const handleConfirmLoader = () => {
    setConfirmedLoader(selectedLoader);
    setIsEditingLoader(false);
  };

  const handleConfirmParser = () => {
    setConfirmedParser(selectedParser);
    setIsEditingParser(false);
  };

  const hasChanges = confirmedLoader !== document?.metadata.loader || confirmedParser !== document?.metadata.parser;

  const handleSave = () => {
    if (document) {
      const updatedDoc = {
        ...document,
        metadata: {
          ...document.metadata,
          loader: confirmedLoader,
          parser: confirmedParser,
          loaderModified: confirmedLoader !== document.metadata.loader || document.metadata.loaderModified,
          parserModified: confirmedParser !== document.metadata.parser || document.metadata.parserModified
        }
      };
      onUpdate(updatedDoc);
      onClose();
    }
  };

  // Document preview functions
  const handleRetry = () => {
    setPreviewLoading(true);
    setPreviewError(null);
    setRenderFailed(false);
    setRetryCount(retryCount + 1);
  };

  const openInNewTab = () => {
    if (document) {
      previewApi.openDocumentInNewTab(document.id);
    }
  };

  const downloadFile = () => {
    if (document) {
      const previewUrl = previewApi.getPreviewUrl(document.id);
      const a = document.createElement('a');
      a.href = previewUrl;
      a.download = document.metadata.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }
  };

  // Handle iframe loading events
  const handleIframeLoad = () => {
    console.log('iframe loaded');
    setPreviewLoading(false);
  };

  const handleIframeError = () => {
    console.log('iframe error');
    setPreviewLoading(false);
    setRenderFailed(true);
  };

  const renderFilePreview = () => {
    if (!document || isFullyClosed) return null;

    // Get the preview URL from the API
    const previewUrl = previewApi.getPreviewUrl(document.id);
    
    // For URL with cache busting
    const urlWithCacheBusting = `${previewUrl}?retry=${retryCount}`;
    
    // Check if file is a PDF
    const isPdf = document.metadata.file_path.toLowerCase().endsWith('.pdf');
    
    // Check if file is an image
    const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(document.metadata.file_path);

    if (previewLoading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      );
    }

    if (previewError) {
      return (
        <div className="flex flex-col items-center justify-center p-6 h-full">
          <div className="text-red-500 mb-4 text-center">{previewError}</div>
          <div className="text-gray-500 mb-4 text-sm text-center">
            File path: {document.metadata.file_path}
          </div>
          <Button variant="outline" onClick={handleRetry}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      );
    }

    if (renderFailed) {
      return (
        <div className="flex flex-col items-center justify-center p-6 h-full">
          <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" />
          <div className="text-lg font-semibold mb-2">Document Preview Blocked</div>
          <div className="text-gray-600 mb-6 text-center max-w-md">
            Your browser has blocked the document preview for security reasons. You can still download or open the document in a new tab.
          </div>
          <div className="flex gap-4">
            <Button variant="outline" onClick={downloadFile}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
            <Button variant="default" onClick={openInNewTab}>
              <ExternalLink className="h-4 w-4 mr-2" />
              Open in New Tab
            </Button>
          </div>
        </div>
      );
    }

    if (isImage) {
      return (
        <div className="flex items-center justify-center p-1 h-full">
          <img 
            src={urlWithCacheBusting} 
            alt={document.metadata.filename}
            className="max-w-full h-auto object-contain"
            onLoad={() => setPreviewLoading(false)}
            onError={() => {
              setPreviewLoading(false);
              setPreviewError("Failed to load image");
            }}
          />
        </div>
      );
    } else if (isPdf) {
      // For PDF rendering, use object tag with iframe fallback for better Chrome compatibility
      return (
        <div className="h-full w-full bg-white">
          <object
            data={urlWithCacheBusting}
            type="application/pdf"
            className="w-full h-full"
            onLoad={handleIframeLoad}
            onError={handleIframeError}
          >
            <iframe
              ref={iframeRef}
              src={`${urlWithCacheBusting}#toolbar=1&view=FitH`}
              className="w-full h-full border-0"
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-downloads"
              allow="fullscreen"
            />
          </object>
        </div>
      );
    } else {
      // For other document types
      return (
        <div className="h-full w-full">
          <iframe
            ref={iframeRef}
            src={urlWithCacheBusting}
            className="w-full h-full border-0"
            onLoad={handleIframeLoad}
            onError={handleIframeError}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-downloads"
            allow="fullscreen"
          />
        </div>
      );
    }
  };

  const renderContent = () => {
    if (isLoading) {
      return <div className="flex justify-center p-4">Loading...</div>;
    }

    if (!document) {
      return <div>No document selected</div>;
    }

    // Return null when fully closed to prevent unnecessary rendering
    if (isFullyClosed) {
      return <div className="hidden"></div>;
    }

    return (
      <div className="flex flex-col lg:flex-row gap-4 h-[calc(100vh-280px)]">
        {/* Left side - File preview */}
        <Card className="flex-1 min-h-[200px] lg:max-w-[50%] overflow-hidden">
          <CardHeader className="p-3 flex flex-row justify-between items-center">
            <CardTitle className="text-lg">Original Document</CardTitle>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={downloadFile} title="Download">
                <Download className="h-4 w-4 mr-1" />
                Download
              </Button>
              <Button variant="outline" size="sm" onClick={openInNewTab} title="Open in new tab">
                <ExternalLink className="h-4 w-4 mr-1" />
                Open in Tab
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0 h-[calc(100vh-380px)]">
            {renderFilePreview()}
          </CardContent>
        </Card>

        {/* Right side - Chunks with new buttons */}
        <Card className="flex-1 min-h-[200px] lg:max-w-[50%]">
          <CardHeader className="p-3">
            <CardTitle className="text-lg">Document Chunks</CardTitle>
          </CardHeader>
          <CardContent className="p-3">
            <ScrollArea className="h-[calc(100vh-380px)]">
              <div className="space-y-3">
                {document.documents.map((chunk, index) => (
                  <div key={index} className="p-3 border rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <div className="text-sm font-medium">
                        Chunk {index + 1}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => {
                            // Add your AI handler here
                            console.log('AI magic for chunk:', index);
                          }}
                        >
                          <Wand2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => {
                            // Add your edit handler here
                            console.log('Edit chunk:', index);
                          }}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 hover:bg-red-100 hover:text-red-600"
                          onClick={() => {
                            // Add your delete handler here
                            console.log('Delete chunk:', index);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown>
                        {chunk.page_content}
                      </ReactMarkdown>
                    </div>
                    <Separator className="my-2" />
                    <div className="text-xs text-muted-foreground break-all">
                      Metadata: {JSON.stringify(chunk.metadata)}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    );
  };

  // Handle closing with cleanup
  const handleModalClose = () => {
    // Clear iframe content before closing
    if (iframeRef.current) {
      try {
        iframeRef.current.src = 'about:blank';
      } catch (e) {
        console.log('Error clearing iframe source', e);
      }
    }
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleModalClose}>
      <DialogContent className="w-[95vw] max-w-7xl h-[90vh] max-h-[90vh] p-6">
        <DialogHeader className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <DialogTitle>{document?.metadata.filename || 'Document Preview'}</DialogTitle>
            {hasChanges && (
              <Button onClick={handleSave} className="px-6">
                Save Changes
              </Button>
            )}
          </div>
            
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-center gap-2">
              {isEditingLoader ? (
                <>
                  <div className="text-sm text-muted-foreground whitespace-nowrap">Loader:</div>
                  <Select value={selectedLoader} onValueChange={handleLoaderChange}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue>{selectedLoader}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {loaders.map(loader => (
                        <SelectItem key={loader} value={loader}>{loader}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button size="icon" variant="ghost" onClick={handleConfirmLoader}>
                    <Check className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  <div className="text-sm text-muted-foreground whitespace-nowrap">Loader:</div>
                  <div className="font-medium">{confirmedLoader}</div>
                  <Button size="icon" variant="ghost" onClick={() => setIsEditingLoader(true)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              {isEditingParser ? (
                <>
                  <div className="text-sm text-muted-foreground whitespace-nowrap">Parser:</div>
                  <Select value={selectedParser} onValueChange={handleParserChange}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue>{selectedParser}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {parsers.map(parser => (
                        <SelectItem key={parser} value={parser}>{parser}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button size="icon" variant="ghost" onClick={handleConfirmParser}>
                    <Check className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  <div className="text-sm text-muted-foreground whitespace-nowrap">Parser:</div>
                  <div className="font-medium">{confirmedParser}</div>
                  <Button size="icon" variant="ghost" onClick={() => setIsEditingParser(true)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          </div>
        </DialogHeader>
        
        {renderContent()}
      </DialogContent>
    </Dialog>
  );
}; 

export default PreviewModal; 