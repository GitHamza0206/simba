import React, { useState } from 'react';
import { Settings, Database, Brain, FileText, ChevronDown, ChevronRight, Info, Scissors } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/context/AuthContext';
import { getAppSettings, AppConfig } from '@/lib/settings_api';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface ChunkingConfig {
  chunk_size: number;
  chunk_overlap: number;
}

interface ExtendedAppConfig extends AppConfig {
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
  const [config, setConfig] = useState<ExtendedAppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  React.useEffect(() => {
    if (!authLoading) {
      fetchConfig();
    }
  }, [authLoading]);

  const fetchConfig = async () => {
    try {
      const data = await getAppSettings();
      setConfig(data as ExtendedAppConfig); // Cast in case chunking is present
      setLoading(false);
    } catch (error: unknown) {
      console.error('Error fetching config:', error);
      let message = 'Failed to load configuration';
      if (error instanceof Error) {
        message = error.message;
      }
      toast({
        title: '错误',
        description: message,
        variant: 'destructive'
      });
      setLoading(false);
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
          <p className="mt-2 text-gray-600">正在加载配置信息...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl mx-auto py-8">
      <div className="flex items-center justify-between mb-8 border-b pb-4">
        <h1 className="text-3xl font-bold text-gray-800">知识配置</h1>
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
                <span className="font-medium text-gray-800">{section.title.replace('Project Configuration', '项目配置').replace('LLM Configuration', '大语言模型配置').replace('Embedding Configuration', '嵌入模型配置').replace('Chunking Configuration', '分块配置').replace('Vector Store Configuration', '向量存储配置').replace('Retrieval Configuration', '检索配置').replace('Database Configuration', '数据库配置').replace('Storage Configuration', '存储配置').replace('Celery Configuration', 'Celery 配置')}</span>
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
                      暂无配置信息
                    </div>
                  )}
                  
                  {section.fields.map((field) => {
                    const isDeprecated = isFieldDeprecated(section.key, field.name);
                    const fieldTitle = field.name
                      .split('_')
                      .map(word => {
                        switch (word) {
                          case 'name': return '名称';
                          case 'version': return '版本';
                          case 'api': return 'API';
                          case 'provider': return '提供商';
                          case 'model': return '模型';
                          case 'key': return '密钥';
                          case 'base': return '基础';
                          case 'url': return 'URL';
                          case 'temperature': return '温度';
                          case 'streaming': return '流式';
                          case 'max': return '最大';
                          case 'tokens': return 'Token数';
                          case 'additional': return '附加';
                          case 'params': return '参数';
                          case 'device': return '设备';
                          case 'collection': return '集合';
                          case 'method': return '方法';
                          case 'k': return 'K值';
                          case 'score': return '分数';
                          case 'threshold': return '阈值';
                          case 'prioritize': return '优先';
                          case 'semantic': return '语义';
                          case 'weights': return '权重';
                          case 'reranker': return '重排序器';
                          case 'bucket': return '桶';
                          case 'secure': return '安全';
                          case 'endpoint': return '端点';
                          case 'access': return '访问';
                          case 'secret': return '密钥';
                          case 'broker': return '代理';
                          case 'result': return '结果';
                          case 'backend': return '后端';
                          case 'chunk': return '分块';
                          case 'size': return '大小';
                          case 'overlap': return '重叠';
                          default: return word.charAt(0).toUpperCase() + word.slice(1);
                        }
                      })
                      .join(' ');
                    
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
                                  <p className="text-xs">此设置在当前配置下不适用。</p>
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