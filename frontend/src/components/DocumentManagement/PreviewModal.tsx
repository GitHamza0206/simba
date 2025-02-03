import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import ReactMarkdown from 'react-markdown';
import { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Pencil, Check, Trash2, Wand2 } from 'lucide-react';
import { ingestionApi } from "@/lib/ingestion_api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Document, Page } from 'react-pdf';

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
  const [isEditingLoader, setIsEditingLoader] = useState(false);
  const [isEditingParser, setIsEditingParser] = useState(false);
  const [selectedLoader, setSelectedLoader] = useState(document?.metadata.loader);
  const [confirmedLoader, setConfirmedLoader] = useState(document?.metadata.loader);
  const [selectedParser, setSelectedParser] = useState(document?.metadata.parser);
  const [confirmedParser, setConfirmedParser] = useState(document?.metadata.parser);
  const [loaders, setLoaders] = useState<string[]>([]);
  const [parsers, setParsers] = useState<string[]>([]);
  const [numPages, setNumPages] = useState<number>(1);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [pdfError, setPdfError] = useState<string | null>(null);

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

  const renderFilePreview = () => {
    if (!document) return null;

    console.log(document);
    const fileType = document.metadata.file_path.split('.').pop()?.toLowerCase();
    
    switch (fileType) {
      case 'pdf':
        return (
          <div className="w-full h-full min-h-[500px]">
            <p>Preview coming soon ...</p>
          </div>
        );
      
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return (
          <img 
            src={document.metadata.file_path}
            alt="Document preview"
            className="max-w-full h-auto"
          />
        );
      
      default:
        return (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>
              {document.content || 'No content available'}
            </ReactMarkdown>
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

    return (
      <div className="flex flex-col lg:flex-row gap-4 h-[calc(100vh-280px)]">
        {/* Left side - File preview */}
        <Card className="flex-1 min-h-[200px] lg:max-w-[50%]">
          <CardHeader className="p-3">
            <CardTitle className="text-lg">Original Document</CardTitle>
          </CardHeader>
          <CardContent className="p-3">
            <ScrollArea className="h-[calc(100vh-380px)]">
              {renderFilePreview()}
            </ScrollArea>
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
                    <div className="prose prose-sm">
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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="w-[95vw] max-w-7xl h-[90vh] max-h-[90vh] p-6">
        <DialogHeader className="space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <DialogTitle>Document Preview</DialogTitle>
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
                      {loaders.map((loader) => (
                        <SelectItem key={loader} value={loader}>
                          {loader}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {/* <Button variant="ghost" size="icon" onClick={handleConfirmLoader}>
                    <Check className="h-4 w-4" />
                  </Button> */}
                </>
              ) : (
                <>
                  <div className="text-sm text-muted-foreground">
                    Loader: {confirmedLoader}
                  </div>
                  {/* <Button variant="ghost" size="icon" onClick={() => setIsEditingLoader(true)}>
                    <Pencil className="h-4 w-4" />
                  </Button> */}
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
                      {parsers.map((parser) => (
                        <SelectItem key={parser} value={parser}>
                          {parser}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {/* <Button variant="ghost" size="icon" onClick={handleConfirmParser}>
                    <Check className="h-4 w-4" />
                  </Button> */}
                </>
              ) : (
                <>
                  <div className="text-sm text-muted-foreground">
                    Parser: {confirmedParser}
                  </div>
                    {/* <Button variant="ghost" size="icon" onClick={() => setIsEditingParser(true)}>
                      <Pencil className="h-4 w-4" />
                    </Button> */}
                </>
              )}
            </div>
          </div>
        </DialogHeader>

        <div className="mt-4">
          {renderContent()}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PreviewModal; 