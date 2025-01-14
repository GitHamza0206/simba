import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import ReactMarkdown from 'react-markdown';
import { useState, useEffect } from 'react';

interface PreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: DocumentType | null;
}

const PreviewModal: React.FC<PreviewModalProps> = ({ 
  isOpen, 
  onClose, 
  document
}) => {
  console.log('Preview Document:', document);

  const [isLoading, setIsLoading] = useState(false);

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
          <DialogTitle>Document Preview</DialogTitle>
          {document?.loader && (
            <div className="text-sm text-muted-foreground">
              Loader: {document?.loader}
            </div>
          )}
        </DialogHeader>
        <div className="mt-4">
          {renderContent()}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PreviewModal; 