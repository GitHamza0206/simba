import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { SimbaDoc } from "@/types/document";
import { parsingApi } from "@/lib/parsing_api";

interface ParserConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  document: SimbaDoc | null;
  onUpdate: (document: SimbaDoc) => void;
}

export function ParserConfigModal({
  isOpen,
  onClose,
  document,
  onUpdate,
}: ParserConfigModalProps) {
  const [selectedParser, setSelectedParser] = useState<string>("");
  const [availableParsers, setAvailableParsers] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Debug logging
  console.log("ParserConfigModal render:", { isOpen, documentId: document?.id });

  // Load available parsers when modal opens
  useEffect(() => {
    console.log("ParserConfigModal useEffect triggered:", { isOpen, documentId: document?.id });
    
    if (isOpen) {
      fetchParsers();
      const currentParser = document?.metadata.parser;
      if (currentParser && typeof currentParser === 'string') {
        setSelectedParser(currentParser);
      } else {
        if (document && currentParser !== undefined) { // Log if it exists but isn't a string
          console.warn(`document.metadata.parser is not a string: ${JSON.stringify(currentParser)}. Defaulting parser.`);
        }
        setSelectedParser("docling"); // Default parser
      }
    }
  }, [isOpen, document]);

  const fetchParsers = async () => {
    setIsLoading(true);
    try {
      const parsers = await parsingApi.getParsers();
      console.log("Fetched parsers:", parsers);
      
      // getParsers already handles the response format and returns a string array
      setAvailableParsers(parsers);
    } catch (error) {
      console.error("Failed to fetch available parsers:", error);
      setAvailableParsers(["docling"]); // Fallback to default parser
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = () => {
    if (!document) return;

    const updatedDoc = {
      ...document,
      metadata: {
        ...document.metadata,
        parser: selectedParser,
      },
    };

    onUpdate(updatedDoc);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose} modal={true}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Parser Configuration{document ? ` - ${document.metadata.filename}` : ''}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="parser" className="text-right">
              Parser
            </Label>
            <Select
              value={selectedParser}
              onValueChange={setSelectedParser}
              disabled={isLoading}
            >
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select a parser" />
              </SelectTrigger>
              <SelectContent>
                {availableParsers.length > 0 ? (
                  availableParsers.map((parser) => (
                    <SelectItem key={parser} value={parser}>
                      {parser}
                    </SelectItem>
                  ))
                ) : (
                  <SelectItem value="docling">docling</SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
          {selectedParser === "mistral_ocr" && (
            <div className="col-span-4 px-1 py-2 text-sm bg-blue-50 rounded-md text-blue-700">
              <p className="font-medium">Mistral OCR Parser</p>
              <p className="mt-1">
                This parser uses Mistral's OCR capabilities to extract text from document images.
                Make sure MISTRAL_API_KEY is set in your environment.
              </p>
            </div>
          )}
          {selectedParser === "docling" && (
            <div className="col-span-4 px-1 py-2 text-sm bg-blue-50 rounded-md text-blue-700">
              <p className="font-medium">Docling Parser</p>
              <p className="mt-1">
                This is the default parser that uses a combination of techniques to extract text from documents.
              </p>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 