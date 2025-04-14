import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Settings2, Save, ChevronDown, ChevronRight, Plus } from 'lucide-react';
import { cn } from "@/lib/utils";

interface ConfigItem {
  label: string;
  value: string | number | boolean | string[];
  type: 'text' | 'number' | 'boolean' | 'list' | 'select';
  options?: string[];
  description?: string;
}

interface ConfigSection {
  title: string;
  items: Record<string, ConfigItem>;
  description?: string;
}

const KnowledgeConfigPage: React.FC = () => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    llmModels: true,
    documentProcessing: false,
    embeddingAndStorage: false,
    retrieval: false
  });
  
  const [config, setConfig] = useState<Record<string, ConfigSection>>({
    llmModels: {
      title: "Language Models",
      description: "Configure which language models are enabled for different tasks",
      items: {
        largeLLMs: {
          label: "Large Language Models",
          value: ["GPT-4", "Claude 3"],
          type: "list",
          description: "High-performance models for complex tasks"
        },
        smallLLMs: {
          label: "Small Language Models",
          value: ["Mistral-7B", "Llama-2"],
          type: "list",
          description: "Efficient models for basic tasks"
        }
      }
    },
    documentProcessing: {
      title: "Document Processing",
      description: "Configure how documents are processed and chunked",
      items: {
        parser: {
          label: "Document Parser",
          value: "Unstructured",
          type: "text",
          description: "Parser used for document extraction"
        },
        chunkSize: {
          label: "Chunk Size",
          value: 5000,
          type: "number",
          description: "Number of characters per chunk"
        },
        chunkOverlap: {
          label: "Chunk Overlap",
          value: 300,
          type: "number",
          description: "Overlap between consecutive chunks"
        }
      }
    },
    embeddingAndStorage: {
      title: "Embedding & Storage",
      description: "Configure embedding models and storage solutions",
      items: {
        embeddingModel: {
          label: "Embedding Model",
          value: "OpenAI Ada 2",
          type: "text",
          description: "Model used for text embeddings"
        },
        graphDB: {
          label: "Graph Database",
          value: true,
          type: "boolean",
          description: "Enable graph database for relationships"
        },
        vectorStore: {
          label: "Vector Store",
          value: "Chroma",
          type: "text",
          description: "Vector database for similarity search"
        }
      }
    },
    retrieval: {
      title: "Retrieval",
      description: "Configure how documents are retrieved",
      items: {
        strategy: {
          label: "Retrieval Strategy",
          value: "Hybrid Search",
          type: "select",
          options: ["Semantic Search", "Keyword Search", "Hybrid Search"],
          description: "Method used to retrieve relevant documents"
        }
      }
    }
  });

  const toggleSection = (sectionKey: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionKey]: !prev[sectionKey]
    }));
  };

  const renderValue = (item: ConfigItem) => {
    if (item.type === 'list') {
      return (
        <div className="flex flex-wrap gap-2">
          {Array.isArray(item.value) ? item.value.map((val, idx) => (
            <div key={idx} className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-sm">
              {val}
            </div>
          )) : item.value}
          <Button variant="ghost" size="sm" className="h-7 px-2">
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      );
    }
    if (item.type === 'boolean') {
      return (
        <div className={cn(
          "px-3 py-1 rounded text-sm",
          item.value ? "bg-green-50 text-green-700" : "bg-gray-50 text-gray-700"
        )}>
          {item.value ? "Enabled" : "Disabled"}
        </div>
      );
    }
    if (item.type === 'select') {
      return (
        <div className="flex items-center gap-2">
          <span className="text-sm">{item.value}</span>
          <ChevronDown className="h-4 w-4 text-gray-500" />
        </div>
      );
    }
    return <span className="text-sm">{item.value}</span>;
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Knowledge Configuration</h1>
      </div>

      <div className="space-y-2">
        {Object.entries(config).map(([sectionKey, section]) => (
          <div key={sectionKey} className="border border-gray-200 bg-white">
            <button
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
              onClick={() => toggleSection(sectionKey)}
            >
              <div className="flex items-center gap-3">
                {expandedSections[sectionKey] ? (
                  <ChevronDown className="h-5 w-5 text-gray-500" />
                ) : (
                  <ChevronRight className="h-5 w-5 text-gray-500" />
                )}
                <div className="text-left">
                  <h2 className="font-medium text-gray-900">{section.title}</h2>
                  {section.description && (
                    <p className="text-sm text-gray-500">{section.description}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" className="h-7">
                  <Settings2 className="h-4 w-4" />
                </Button>
              </div>
            </button>
            
            {expandedSections[sectionKey] && (
              <div className="px-12 pb-4 space-y-4">
                {Object.entries(section.items).map(([itemKey, item]) => (
                  <div key={itemKey} className="flex items-center justify-between py-2">
                    <div>
                      <div className="font-medium text-gray-700">{item.label}</div>
                      {item.description && (
                        <div className="text-sm text-gray-500">{item.description}</div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {renderValue(item)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default KnowledgeConfigPage; 