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
  console.log('Preview Document:', document);

  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedLoader, setSelectedLoader] = useState(document?.loader);
  const [confirmedLoader, setConfirmedLoader] = useState(document?.loader);
  const [loaders, setLoaders] = useState<string[]>([]);
  const [hasEdited, setHasEdited] = useState(false);

  useEffect(() => {
    const fetchLoaders = async () => {
      const response = await ingestionApi.getLoaders();
      setLoaders(response.loaders);
    };
    fetchLoaders();
  }, []);

  useEffect(() => {
    setSelectedLoader(document?.loader);
    setConfirmedLoader(document?.loader);
    setHasEdited(false);
  }, [document]);

  const handleLoaderChange = (value: string) => {
    setSelectedLoader(value);
    setHasEdited(true);
  };

  const handleConfirmLoader = () => {
    setConfirmedLoader(selectedLoader);
    setIsEditing(false);
  };

  const handleSave = () => {
    if (document) {
      const updatedDoc = {
        ...document,
        loader: confirmedLoader,
        loaderModified: true
      };
      onUpdate(updatedDoc);
      setHasEdited(false);
      onClose();
    }
  };

  const showSaveButton = hasEdited && confirmedLoader !== document?.loader;

  const renderContent = () => {
    if (isLoading) {
      return <div className="flex justify-center p-4">Loading...</div>;
    }

    if (!document) {
      return <div>No document selected</div>;
    }

    if (document.type === 'pdf') {
      return (
        <iframe
          src={`data:application/pdf;base64,${document.content}`}
          className="w-full h-[70vh]"
          title="PDF Preview"
        />
      );
    }
    
    return (
      <ReactMarkdown className="prose prose-sm max-w-none">
        {document.content || 'No content available'}
      </ReactMarkdown>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex justify-between items-center">
            <DialogTitle>Document Preview</DialogTitle>
            {showSaveButton && (
              <Button onClick={handleSave} className="px-6 mr-8">
                Save Changes
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            {isEditing ? (
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
                <Button variant="ghost" size="icon" onClick={() => setIsEditing(true)}>
                  <Pencil className="h-4 w-4" />
                </Button>
              </>
            )}
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