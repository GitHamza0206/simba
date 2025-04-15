import React, { useState } from 'react';
import { Settings, Database, Brain, FileText, ChevronDown, ChevronRight, Info, Scissors } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/context/AuthContext';
import { getAccessToken } from '@/lib/supabase';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface LLMConfig {
  provider: string;
  model_name: string;
  api_key?: string;
  base_url?: string;
  temperature: number;
  streaming: boolean;
  max_tokens: number | null;
  additional_params: Record<string, unknown>;
}

interface EmbeddingConfig {
  provider: string;
  model_name: string;
  device: string;
  additional_params: Record<string, unknown>;
}

interface VectorStoreConfig {
  provider: string;
  collection_name: string;
  additional_params: Record<string, unknown>;
}

interface RetrievalParams {
  score_threshold: number;
  prioritize_semantic: boolean;
  weights: number[];
  reranker_model: string;
  reranker_threshold: number;
}

interface RetrievalConfig {
  method: string;
  k: number;
  params: RetrievalParams;
}

interface ProjectConfig {
  name: string;
  version: string;
  api_version: string;
}

interface DatabaseConfig {
  provider: string;
  additional_params: Record<string, unknown>;
}

interface StorageConfig {
  provider: string;
  minio_endpoint?: string;
  minio_access_key?: string;
  minio_secret_key?: string;
  minio_bucket?: string;
  minio_secure?: boolean;
}

interface CeleryConfig {
  broker_url: string;
  result_backend: string;
}

interface ChunkingConfig {
  chunk_size: number;
  chunk_overlap: number;
}

interface Config {
  llm?: LLMConfig;
  embedding?: EmbeddingConfig;
  vector_store?: VectorStoreConfig;
  retrieval?: RetrievalConfig;
  project?: ProjectConfig;
  database?: DatabaseConfig;
  storage?: StorageConfig;
  celery?: CeleryConfig;
  chunking?: ChunkingConfig;
}

interface ConfigSection {
  title: string;
  icon: React.ReactNode;
  key: string;
  fields: {
    name: string;
    value: string | number | boolean | null | unknown[] | Record<string, unknown>;
  }[];
}

export default function KnowledgeConfigPage() {
  const { toast } = useToast();
  const { loading: authLoading } = useAuth();
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  React.useEffect(() => {
    if (!authLoading) {
      fetchConfig();
    }
  }, [authLoading]);

  const fetchConfig = async () => {
    try {
      const token = getAccessToken();
      const response = await fetch('/api/config', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      setConfig(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching config:', error);
      toast({
        title: 'Error',
        description: 'Failed to load configuration',
        variant: 'destructive'
      });
    }
  };

  // Format the JSON value for display
  const formatValue = (value: unknown): string => {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    
    return String(value);
  };

  // Handle special cases for sensitive data
  const displayValue = (key: string, value: unknown): string => {
    // Mask API keys and sensitive information
    if (
      key.includes('api_key') || 
      key.includes('secret_key') || 
      key.includes('password') || 
      key.includes('token')
    ) {
      return value ? '••••••••••••••••••••••' : '';
    }
    
    return formatValue(value);
  };

  // Check if a field should be displayed with strikethrough
  const isFieldDeprecated = (section: string, fieldName: string): boolean => {
    // base_url is only applicable for ollama provider
    if (section === 'llm' && fieldName === 'base_url' && config?.llm?.provider !== 'ollama') {
      return true;
    }
    return false;
  };

  const configSections: ConfigSection[] = [
    {
      title: 'Project Configuration',
      icon: <FileText className="h-5 w-5" />,
      key: 'project',
      fields: config?.project
        ? Object.entries(config.project).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'LLM Configuration',
      icon: <Brain className="h-5 w-5" />,
      key: 'llm',
      fields: config?.llm
        ? Object.entries(config.llm).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Embedding Configuration',
      icon: <FileText className="h-5 w-5" />,
      key: 'embedding',
      fields: config?.embedding
        ? Object.entries(config.embedding).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Chunking Configuration',
      icon: <Scissors className="h-5 w-5" />,
      key: 'chunking',
      fields: config?.chunking
        ? Object.entries(config.chunking).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Vector Store Configuration',
      icon: <Database className="h-5 w-5" />,
      key: 'vector_store',
      fields: config?.vector_store
        ? Object.entries(config.vector_store).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Retrieval Configuration',
      icon: <Settings className="h-5 w-5" />,
      key: 'retrieval',
      fields: config?.retrieval
        ? Object.entries(config.retrieval).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Database Configuration',
      icon: <Database className="h-5 w-5" />,
      key: 'database',
      fields: config?.database
        ? Object.entries(config.database).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Storage Configuration',
      icon: <Settings className="h-5 w-5" />,
      key: 'storage',
      fields: config?.storage
        ? Object.entries(config.storage)
            .filter(([key]) => {
              // If storage provider is local, hide minio-related fields
              if (config.storage?.provider === 'local' && key.includes('minio_')) {
                return false;
              }
              return true;
            })
            .map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Celery Configuration',
      icon: <Settings className="h-5 w-5" />,
      key: 'celery',
      fields: config?.celery
        ? Object.entries(config.celery).map(([name, value]) => ({ name, value }))
        : [],
    },
  ];

  const renderConfigValue = (name: string, value: unknown, isDeprecated: boolean) => {
    // Check if value is an object or array
    const isComplexValue = typeof value === 'object' && value !== null;
    
    return (
      <div className={`text-sm break-all font-mono rounded-md ${isDeprecated ? 'line-through text-gray-400' : 'text-gray-800'}`}>
        {isComplexValue ? (
          <div className="bg-gray-50 p-3 rounded-md overflow-auto max-h-60">
            <pre className="whitespace-pre-wrap">{displayValue(name, value)}</pre>
          </div>
        ) : (
          <div className="bg-gray-50 p-3 rounded-md">
            {displayValue(name, value)}
          </div>
        )}
      </div>
    );
  };

  if (loading || authLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl mx-auto py-8">
      <div className="flex items-center justify-between mb-8 border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-800">Knowledge Configuration</h1>
      </div>
      
      <div className="space-y-4">
        {configSections.map((section) => (
          <div key={section.key} className="border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <button
              onClick={() => setExpandedSection(expandedSection === section.key ? null : section.key)}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-md bg-gray-100">
                  {section.icon}
                </div>
                <span className="font-medium text-gray-800">{section.title}</span>
              </div>
              <div className="text-gray-400">
                {expandedSection === section.key ? (
                  <ChevronDown className="h-5 w-5" />
                ) : (
                  <ChevronRight className="h-5 w-5" />
                )}
              </div>
            </button>
            
            {expandedSection === section.key && (
              <div className="p-5 border-t border-gray-200 bg-white">
                <div className="space-y-5">
                  {section.fields.length === 0 && (
                    <div className="text-gray-400 text-sm bg-gray-50 p-4 rounded-md">
                      No configuration data available
                    </div>
                  )}
                  
                  {section.fields.map((field) => {
                    const isDeprecated = isFieldDeprecated(section.key, field.name);
                    const fieldTitle = field.name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                    
                    return (
                      <div key={field.name} className="flex flex-col gap-2 pb-4 border-b border-gray-100 last:border-0">
                        <div className="flex items-center gap-2">
                          <Label className={`text-sm font-medium ${isDeprecated ? 'line-through text-gray-400' : 'text-gray-700'}`}>
                            {fieldTitle}
                          </Label>
                          
                          {isDeprecated && (
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>
                                  <Info className="h-4 w-4 text-gray-400" />
                                </TooltipTrigger>
                                <TooltipContent>
                                  <p className="text-xs">This setting is not applicable with the current configuration.</p>
                                </TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          )}
                        </div>
                        
                        {renderConfigValue(field.name, field.value, isDeprecated)}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
} 