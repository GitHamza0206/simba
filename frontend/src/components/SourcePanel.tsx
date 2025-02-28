import React, { useState, useEffect } from 'react';
import { Message } from '@/types/chat';
import { FileText, Book, AlertCircle, ExternalLink } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { previewApi } from '@/lib/api_services';

interface SourcePanelProps {
  message: Message;
}

interface GroupedSource {
  file_name: string;
  count: number;
  relevance?: number;
  content?: string;
  page?: number;
}

const SourcePanel: React.FC<SourcePanelProps> = ({ message }) => {
  const [groupedSources, setGroupedSources] = useState<GroupedSource[]>([]);
  const [selectedSource, setSelectedSource] = useState<GroupedSource | null>(null);
  const [loading, setLoading] = useState(false);

  // Group sources by file name and count them
  useEffect(() => {
    if (!message?.state?.sources) return;
    
    const sources = message.state.sources;
    const sourceMap = new Map<string, GroupedSource>();
    
    sources.forEach(source => {
      if (!source.file_name) return;
      
      if (sourceMap.has(source.file_name)) {
        const existing = sourceMap.get(source.file_name)!;
        sourceMap.set(source.file_name, {
          ...existing,
          count: existing.count + 1,
          // Use the highest relevance score if available
          relevance: Math.max(existing.relevance || 0, source.relevance || 0)
        });
      } else {
        sourceMap.set(source.file_name, {
          file_name: source.file_name,
          count: 1,
          relevance: source.relevance,
          content: source.content,
          page: source.page
        });
      }
    });
    
    // Convert to array and sort by relevance/count
    const groupedArray = Array.from(sourceMap.values()).sort((a, b) => {
      // First by relevance if available
      if (a.relevance !== undefined && b.relevance !== undefined) {
        return b.relevance - a.relevance;
      }
      // Then by count
      return b.count - a.count;
    });
    
    setGroupedSources(groupedArray);
    
    // Select the first source by default
    if (groupedArray.length > 0 && !selectedSource) {
      setSelectedSource(groupedArray[0]);
    }
  }, [message, selectedSource]);

  // Get just the filename from a full path
  const getFileName = (path: string) => {
    return path.split('/').pop() || path;
  };

  // Get file extension
  const getFileExtension = (filename: string) => {
    return filename.split('.').pop()?.toLowerCase() || '';
  };

  // Open file in preview
  const openFilePreview = (source: GroupedSource) => {
    // Extract document ID from the filename path pattern
    // This assumes your filenames contain the document ID in a predictable format
    // You may need to adjust this based on your actual filename format
    const parts = source.file_name.split('/');
    const filename = parts[parts.length - 1];
    const idMatch = filename.match(/^(\w+)_/);
    
    if (idMatch && idMatch[1]) {
      const documentId = idMatch[1];
      try {
        window.open(previewApi.getPreviewUrl(documentId), '_blank');
      } catch (error) {
        console.error('Failed to open preview:', error);
      }
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <ScrollArea className="flex-1 py-2 px-2 sm:px-3 overflow-auto">
        <div className="space-y-4">
          {groupedSources.length === 0 ? (
            <div className="flex flex-col items-center justify-center text-center p-6 text-gray-500">
              <AlertCircle className="h-10 w-10 mb-2" />
              <h3 className="font-medium">No sources available</h3>
              <p className="text-sm">This message doesn't have any source information.</p>
            </div>
          ) : (
            <>
              <div className="flex flex-col gap-2">
                {groupedSources.map((source, index) => (
                  <Card 
                    key={index} 
                    className={`cursor-pointer hover:border-blue-300 transition-colors ${selectedSource?.file_name === source.file_name ? 'border-blue-400 bg-blue-50' : ''}`}
                    onClick={() => setSelectedSource(source)}
                  >
                    <CardContent className="p-2 sm:p-3">
                      <div className="flex items-start gap-2">
                        <div className="p-1.5 sm:p-2 bg-blue-100 rounded-md text-blue-600 shrink-0">
                          <FileText className="h-4 w-4 sm:h-5 sm:w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div 
                            className="font-medium text-xs sm:text-sm line-clamp-2"
                            title={getFileName(source.file_name)}
                          >
                            {getFileName(source.file_name)}
                          </div>
                          <div className="text-xs text-gray-500 mt-1 flex flex-wrap gap-1 sm:gap-2">
                            <Badge variant="outline" className="px-1 py-0 h-4 sm:h-5 text-[10px] sm:text-xs shrink-0">
                              {getFileExtension(source.file_name).toUpperCase()}
                            </Badge>
                            <span className="text-[10px] sm:text-xs whitespace-nowrap">
                              Cited {source.count} {source.count === 1 ? 'time' : 'times'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {selectedSource && (
                <div className="mt-4 sm:mt-6">
                  <div className="flex flex-col mb-2">
                    <h3 className="font-medium text-xs sm:text-sm break-words pr-2 mb-2">
                      {getFileName(selectedSource.file_name)}
                    </h3>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="px-1 py-0 h-4 sm:h-5 text-[10px] sm:text-xs">
                          {getFileExtension(selectedSource.file_name).toUpperCase()}
                        </Badge>
                        {selectedSource.page !== undefined && (
                          <span className="text-[10px] sm:text-xs text-gray-500">
                            Page {selectedSource.page}
                          </span>
                        )}
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-6 sm:h-8 px-1.5 sm:px-2 text-[10px] sm:text-xs whitespace-nowrap shrink-0"
                        onClick={() => openFilePreview(selectedSource)}
                      >
                        <ExternalLink className="h-3 w-3 sm:h-3.5 sm:w-3.5 mr-1" />
                        Open document
                      </Button>
                    </div>
                  </div>
                  <Separator className="my-2" />
                  <div className="bg-gray-50 p-2 sm:p-3 rounded-md text-xs sm:text-sm border border-gray-200 whitespace-pre-wrap break-words max-h-[200px] sm:max-h-[300px] overflow-y-auto">
                    {selectedSource.content || (
                      <div className="text-gray-500 italic">Content preview not available</div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

export default SourcePanel; 