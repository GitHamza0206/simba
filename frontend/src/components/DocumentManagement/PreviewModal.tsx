import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css'; // Import KaTeX CSS
import { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Wand2, Download, ExternalLink, RefreshCw, AlertTriangle } from 'lucide-react';
import { previewApi } from "@/lib/api_services";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { SimbaDoc, Document } from "@/types/document"; // Ensure SimbaDoc and Document are imported

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: SimbaDoc | null;
}

// Add CSS styles at the component level
const imageStyles = `
  img {
    max-width: 100% !important;
    height: auto !important;
    margin: 10px 0 !important;
    display: block !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 0.375rem !important;
  }
`;

// Add enhanced KaTeX styles
const mathStyles = `
  .katex {
    font-size: 1.1em !important;
    line-height: 1.5 !important;
  }
  .katex-display {
    margin: 1em 0 !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
  }
  .math-inline {
    padding: 0 0.15em !important;
  }
`;

const PreviewModal: React.FC<PreviewModalProps> = ({ 
  isOpen, 
  onClose, 
  document
}) => {
  const [isLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(true);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [renderFailed, setRenderFailed] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [isFullyClosed, setIsFullyClosed] = useState(!isOpen);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [previewSrc, setPreviewSrc] = useState<string | null>(null);

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

  // Fetch preview blob with auth when document changes
  useEffect(() => {
    const fetchPreview = async () => {
      if (!document) return;
      try {
        setPreviewLoading(true);
        const blob = await previewApi.fetchPreviewBlob(document.id);
        const url = URL.createObjectURL(blob);
        setPreviewSrc(url);
      } catch (err: unknown) {
        console.error('Failed to fetch preview blob:', err);
        const message = err instanceof Error ? err.message : 'Failed to load preview';
        setPreviewError(message);
        setRenderFailed(true);
      } finally {
        setPreviewLoading(false);
      }
    };
    fetchPreview();
    // Revoke URL on cleanup
    return () => {
      if (previewSrc) URL.revokeObjectURL(previewSrc);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [document, retryCount]);

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
      const anchor = window.document.createElement('a');
      anchor.href = previewUrl;
      anchor.download = document.metadata.filename;
      window.document.body.appendChild(anchor);
      anchor.click();
      window.document.body.removeChild(anchor);
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
    const urlWithCacheBusting = previewSrc ? `${previewSrc}#${retryCount}` : '';
    
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

    if (isImage && previewSrc) {
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
    } else if (isPdf && previewSrc) {
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
              src={urlWithCacheBusting}
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
          {previewSrc && (
            <iframe
              ref={iframeRef}
              src={urlWithCacheBusting}
              className="w-full h-full border-0"
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-downloads"
              allow="fullscreen"
            />
          )}
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
      <div className="flex flex-col lg:flex-row gap-4 flex-1 overflow-hidden">
        {/* Left side - File preview */}
        <Card className="flex-1 min-h-[200px] lg:max-w-[50%] flex flex-col overflow-hidden">
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
          <CardContent className="p-0 flex-1 overflow-hidden">
            {renderFilePreview()}
          </CardContent>
        </Card>

        {/* Right side - Chunks with new buttons */}
        <Card className="flex-1 min-h-[200px] lg:max-w-[50%] flex flex-col overflow-hidden">
          <CardHeader className="p-3">
            <CardTitle className="text-lg">Document Chunks</CardTitle>
          </CardHeader>
          <CardContent className="p-3 flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="space-y-3">
                {document.documents.map((chunk: Document, index: number) => (
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
                      <ChunkContent content={(chunk.page_content ?? chunk.content) as string} />
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
      <DialogContent className="w-[95vw] max-w-7xl h-[90vh] max-h-[90vh] p-6 flex flex-col">
        <DialogHeader className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <DialogTitle>{document?.metadata.filename || 'Document Preview'}</DialogTitle>
          </div>
          {/* Add summary display if present */}
          {document?.metadata.summary && (
            <div className="flex flex-col w-full">
              <div className="text-sm text-muted-foreground whitespace-nowrap font-semibold mb-1">Summary:</div>
              <div
                className="text-sm bg-muted rounded p-2 border border-muted-foreground/10 max-w-2xl whitespace-pre-line overflow-auto"
                style={{ maxHeight: '180px' }}
              >
                {document.metadata.summary}
              </div>
            </div>
          )}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="text-sm text-muted-foreground whitespace-nowrap">Loader:</div>
              <div className="font-medium">{document?.metadata.loader}</div>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="text-sm text-muted-foreground whitespace-nowrap">Parser:</div>
              <div className="font-medium">{document?.metadata.parser}</div>
            </div>
          </div>
        </DialogHeader>
        
        {renderContent()}
      </DialogContent>
    </Dialog>
  );
};

// Add this custom component inside the PreviewModal component
const ChunkContent = ({ content }: { content: string }) => {
  // For safety, verify content is a string
  if (typeof content !== 'string') {
    return <div>Invalid content</div>;
  }

  // Check if content contains LaTeX-style math that would benefit from KaTeX
  const hasMathContent = /\$.*?\$|\${2}.*?\${2}/g.test(content);
  
  // Check if content contains image markdown syntax that needs special handling
  const hasImageSyntax = /!\[(.*?)\]\((data:image\/[^)]+)\)/g.test(content);

  // If we detect image syntax, use the original rendering method which worked for images
  if (hasImageSyntax) {
    // For content with images, process it using our basic formatter
    const processedContent = content
      // Manually format superscript notation for math/citations
      .replace(/\$\{\s*\}\^{([^}]+)}\$/g, '<sup>$1</sup>')
      // Handle other LaTeX-style formatting that might appear
      .replace(/\$\^{([^}]+)}\$/g, '<sup>$1</sup>')
      .replace(/\$_{([^}]+)}\$/g, '<sub>$1</sub>');
      
    return (
      <>
        <style>{imageStyles}</style>
        <div 
          className="prose prose-sm max-w-none overflow-auto p-2"
          dangerouslySetInnerHTML={{ 
            __html: processedContent
              // Convert markdown image syntax to HTML for reliable rendering
              .replace(/!\[(.*?)\]\((data:image\/[^)]+)\)/g, '<img src="$2" alt="$1" />')
              // Add line breaks for better readability
              .replace(/\n/g, '<br />')
          }} 
        />
      </>
    );
  }
  
  // For complex math content, use the full KaTeX renderer
  if (hasMathContent) {
    return (
      <>
        <style>{imageStyles}</style>
        <style>{mathStyles}</style>
        <ReactMarkdown
          className="prose prose-sm max-w-none overflow-auto p-2"
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeRaw, rehypeSanitize, [rehypeKatex, { output: 'html' }]]}
        >
          {content}
        </ReactMarkdown>
      </>
    );
  }
  
  // For regular content without math or images, use normal markdown
  // But still apply the simple formatting to handle basic superscripts
  const processedContent = content
    // Manually format superscript notation for math/citations in case KaTeX isn't working
    .replace(/\$\{\s*\}\^{([^}]+)}\$/g, '<sup>$1</sup>')
    .replace(/\$\^{([^}]+)}\$/g, '<sup>$1</sup>')
    .replace(/\$_{([^}]+)}\$/g, '<sub>$1</sub>');
    
  return (
    <>
      <style>{imageStyles}</style>
      <ReactMarkdown
        className="prose prose-sm max-w-none overflow-auto p-2"
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeSanitize]}
      >
        {processedContent}
      </ReactMarkdown>
    </>
  );
};

export default PreviewModal; 