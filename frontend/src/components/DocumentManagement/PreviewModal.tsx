import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import ReactMarkdown from 'react-markdown';
import { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Pencil, Check } from 'lucide-react';
import { ingestionApi } from "@/lib/ingestion_api";
interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: DocumentType | null;
  onUpdate: (document: DocumentType) => void;
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
  const [selectedLoader, setSelectedLoader] = useState(document?.loader);
  const [confirmedLoader, setConfirmedLoader] = useState(document?.loader);
  const [selectedParser, setSelectedParser] = useState(document?.parser);
  const [confirmedParser, setConfirmedParser] = useState(document?.parser);
  const [loaders, setLoaders] = useState<string[]>([]);
  const [parsers, setParsers] = useState<string[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [loadersResponse, parsersResponse] = await Promise.all([
          ingestionApi.getLoaders(),
          ingestionApi.getParsers()
        ]);
        setLoaders(loadersResponse.loaders);
        setParsers(parsersResponse.parsers);
      } catch (error) {
        console.error('Error fetching loaders and parsers:', error);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    setSelectedLoader(document?.loader);
    setConfirmedLoader(document?.loader);
    setSelectedParser(document?.parser);
    setConfirmedParser(document?.parser);
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

  const hasChanges = confirmedLoader !== document?.loader || confirmedParser !== document?.parser;

  const handleSave = () => {
    if (document) {
      const updatedDoc = {
        ...document,
        loader: confirmedLoader,
        parser: confirmedParser,
        loaderModified: confirmedLoader !== document.loader || document.loaderModified,
        parserModified: confirmedParser !== document.parser || document.parserModified
      };
      onUpdate(updatedDoc);
      onClose();
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
      <div>
        <div className="flex items-center gap-2 mb-4">
          <h3 className="text-base font-medium text-slate-900">
            Document Content
          </h3>
          <Button variant="ghost" size="icon" className="h-6 w-6">
            <Pencil className="h-4 w-4" />
          </Button>
        </div>
        
        <ReactMarkdown className="prose prose-sm max-w-none">
          {document.content || 'No content available'}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex justify-between items-center">
            <DialogTitle>Document Preview</DialogTitle>
            {hasChanges && (
              <Button onClick={handleSave} className="px-6 mr-8">
                Save Changes
              </Button>
            )}
          </div>
            
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {isEditingLoader ? (
                <>
                  <div className="text-sm text-muted-foreground">Loader:</div>
                  <Select value={selectedLoader} onValueChange={handleLoaderChange}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue>{selectedLoader}</SelectValue>
                    </SelectTrigger>
                    <SelectContent defaultValue={document?.loader}>
                      {loaders.map((loader) => (
                        <SelectItem key={loader} value={loader}>
                          {loader}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" onClick={handleConfirmLoader}>
                    <Check className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  <div className="text-sm text-muted-foreground">
                    Loader: {confirmedLoader}
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => setIsEditingLoader(true)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>

            <div className="flex items-center gap-2">
              {isEditingParser ? (
                <>
                  <div className="text-sm text-muted-foreground">Parser:</div>
                  <Select value={selectedParser} onValueChange={handleParserChange}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue>{selectedParser}</SelectValue>
                    </SelectTrigger>
                    <SelectContent defaultValue={document?.parser}>
                      {parsers.map((parser) => (
                        <SelectItem key={parser} value={parser}>
                          {parser}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button variant="ghost" size="icon" onClick={handleConfirmParser}>
                    <Check className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  <div className="text-sm text-muted-foreground">
                    Parser: {confirmedParser}
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => setIsEditingParser(true)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
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