import React, { useState } from 'react';
import { Settings, Database, Brain, FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/context/AuthContext';
import { getAccessToken } from '@/lib/supabase';

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

interface Config {
  llm?: LLMConfig;
  embedding?: EmbeddingConfig;
  vector_store?: VectorStoreConfig;
  retrieval?: RetrievalConfig;
  project?: ProjectConfig;
  database?: DatabaseConfig;
  storage?: StorageConfig;
  celery?: CeleryConfig;
}

interface ConfigSection {
  title: string;
  icon: React.ReactNode;
  key: string;
  shortcut: string;
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

  const configSections: ConfigSection[] = [
    {
      title: 'LLM Configuration',
      icon: <Brain className="h-5 w-5" />,
      key: 'llm',
      shortcut: '⌘ + 1',
      fields: config?.llm
        ? Object.entries(config.llm).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Embedding Configuration',
      icon: <FileText className="h-5 w-5" />,
      key: 'embedding',
      shortcut: '⌘ + 2',
      fields: config?.embedding
        ? Object.entries(config.embedding).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Vector Store Configuration',
      icon: <Database className="h-5 w-5" />,
      key: 'vector_store',
      shortcut: '⌘ + 3',
      fields: config?.vector_store
        ? Object.entries(config.vector_store).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Retrieval Configuration',
      icon: <Settings className="h-5 w-5" />,
      key: 'retrieval',
      shortcut: '⌘ + 4',
      fields: config?.retrieval
        ? Object.entries(config.retrieval).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Project Configuration',
      icon: <FileText className="h-5 w-5" />,
      key: 'project',
      shortcut: '⌘ + 5',
      fields: config?.project
        ? Object.entries(config.project).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Database Configuration',
      icon: <Database className="h-5 w-5" />,
      key: 'database',
      shortcut: '⌘ + 6',
      fields: config?.database
        ? Object.entries(config.database).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Storage Configuration',
      icon: <Settings className="h-5 w-5" />,
      key: 'storage',
      shortcut: '⌘ + 7',
      fields: config?.storage
        ? Object.entries(config.storage).map(([name, value]) => ({ name, value }))
        : [],
    },
    {
      title: 'Celery Configuration',
      icon: <Settings className="h-5 w-5" />,
      key: 'celery',
      shortcut: '⌘ + 8',
      fields: config?.celery
        ? Object.entries(config.celery).map(([name, value]) => ({ name, value }))
        : [],
    },
  ];

  if (loading || authLoading) {
    return <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-2">Loading configuration...</p>
      </div>
    </div>;
  }

  return (
    <div className="container max-w-3xl mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Knowledge Configuration</h1>
      </div>
      <div className="space-y-2">
        {configSections.map((section) => (
          <div key={section.key} className="rounded-none border border-gray-200">
            <button
              onClick={() => setExpandedSection(expandedSection === section.key ? null : section.key)}
              className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                {section.icon}
                <span className="font-medium">{section.title}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500">{section.shortcut}</span>
                {expandedSection === section.key ? (
                  <ChevronDown className="h-5 w-5" />
                ) : (
                  <ChevronRight className="h-5 w-5" />
                )}
              </div>
            </button>
            {expandedSection === section.key && (
              <div className="p-4 border-t border-gray-200 bg-white">
                <div className="space-y-4">
                  {section.fields.length === 0 && (
                    <div className="text-gray-400 text-sm">No data</div>
                  )}
                  {section.fields.map((field) => (
                    <div key={field.name} className="flex flex-col gap-1">
                      <Label className="text-sm font-medium">
                        {field.name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                      </Label>
                      <div className="text-gray-800 text-sm break-all font-mono bg-gray-50 p-2 rounded">
                        {displayValue(field.name, field.value)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
} 