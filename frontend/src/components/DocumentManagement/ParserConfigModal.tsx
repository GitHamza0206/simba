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
import { ingestionApi } from "@/lib/ingestion_api";

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

  // Load available parsers when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchParsers();
      if (document?.metadata.parser) {
        setSelectedParser(document.metadata.parser);
      } else {
        setSelectedParser("docling"); // Default parser
      }
    }
  }, [isOpen, document]);

  const fetchParsers = async () => {
    setIsLoading(true);
    try {
      const parsers = await ingestionApi.getParsers();
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
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Parser Configuration</DialogTitle>
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
                {availableParsers.map((parser) => (
                  <SelectItem key={parser} value={parser}>
                    {parser}
                  </SelectItem>
                ))}
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