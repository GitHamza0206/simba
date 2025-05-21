import React, { useState, useEffect } from 'react';
import { apiKeyService } from '@/lib/api_services';
import type { ApiKey, ApiKeyResponse, ApiKeyCreate } from '@/lib/api_services';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/context/AuthContext';
import { Button } from "@/components/ui/button";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2, Copy, Clock, CheckCircle, XCircle } from "lucide-react";
import { format } from 'date-fns';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

export default function ApiKeysPage() {
  const { toast } = useToast();
  const { loading: authLoading, user } = useAuth();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState('');
  const [isCreatingKey, setIsCreatingKey] = useState(false);
  const [newApiKey, setNewApiKey] = useState<ApiKeyResponse | null>(null);
  const [deleteKeyId, setDeleteKeyId] = useState<string | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  // Get user ID from user context
  const userId = user?.id;

  useEffect(() => {
    if (!authLoading) {
      fetchApiKeys();
    }
  }, [authLoading, userId]);

  const fetchApiKeys = async () => {
    try {
      setLoading(true);
      const keys = await apiKeyService.getApiKeys(userId);
      setApiKeys(keys);
    } catch (error) {   
      console.error('Error fetching API keys:', error);
      toast({
        title: '错误',
        description: '加载 API 密钥失败',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async () => {
    if (!newKeyName.trim()) {
      toast({
        title: '错误',
        description: '请为 API 密钥提供名称',
        variant: 'destructive'
      });
      return;
    }

    try {
      setIsCreatingKey(true);
      const keyData: ApiKeyCreate = {
        name: newKeyName.trim(),
        tenant_id: userId
      };
      
      const response = await apiKeyService.createApiKey(keyData);
      setNewApiKey(response);
      
      // Refresh the list of API keys
      await fetchApiKeys();
      
      toast({
        title: '成功',
        description: 'API 密钥创建成功',
      });
      
      // Clear input field
      setNewKeyName('');
    } catch (error) {
      console.error('Error creating API key:', error);
      toast({
        title: '错误',
        description: '创建 API 密钥失败',
        variant: 'destructive'
      });
    } finally {
      setIsCreatingKey(false);
    }
  };

  const handleDeleteApiKey = async (keyId: string) => {
    setDeleteKeyId(keyId);
    setIsDeleteDialogOpen(true);
  };

  const confirmDeleteApiKey = async () => {
    if (!deleteKeyId) return;
    
    try {
      await apiKeyService.deleteApiKey(deleteKeyId, userId);
      
      // Refresh the list of API keys
      await fetchApiKeys();
      
      toast({
        title: '成功',
        description: 'API 密钥删除成功',
      });
    } catch (error) {
      console.error('Error deleting API key:', error);
      toast({
        title: '错误',
        description: '删除 API 密钥失败',
        variant: 'destructive'
      });
    } finally {
      setIsDeleteDialogOpen(false);
      setDeleteKeyId(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        toast({
          title: '已复制',
          description: 'API 密钥已复制到剪贴板',
        });
      })
      .catch((error) => {
        console.error('Failed to copy:', error);
        toast({
          title: '错误',
          description: '复制到剪贴板失败',
          variant: 'destructive'
        });
      });
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return '无';
    try {
      return format(new Date(dateString), 'yyyy年M月d日 HH:mm');
    } catch {
      return '无效日期';
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-screen-xl">
      <div className="flex flex-col mb-8">
        <h1 className="text-2xl font-bold">API 密钥</h1>
        <p className="text-gray-500 mt-1">
          创建和管理用于以编程方式访问您账户的 API 密钥。
        </p>
      </div>

      {/* New API Key Card */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>创建新的 API 密钥</CardTitle>
          <CardDescription>
            创建新的 API 密钥以通过编程方式访问 API。API 密钥在被撤销前一直有效。
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-grow">
              <Label htmlFor="new-key-name">API 密钥名称</Label>
              <Input
                id="new-key-name"
                placeholder="例如：开发环境、生产环境等"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                disabled={isCreatingKey}
              />
            </div>
            <div className="flex items-end">
              <Button 
                onClick={handleCreateApiKey} 
                disabled={isCreatingKey || !newKeyName.trim()}
              >
                {isCreatingKey ? '正在创建...' : '创建 API 密钥'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Newly Created API Key */}
      {newApiKey && (
        <Card className="mb-8 border-green-500">
          <CardHeader className="bg-green-50">
            <CardTitle className="text-green-600 flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              API 密钥创建成功
            </CardTitle>
            <CardDescription>
              请立即复制您的 API 密钥。您将无法再次查看！
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="bg-gray-50 p-4 rounded-md flex items-center justify-between border">
              <code className="text-sm font-mono break-all">{newApiKey.key}</code>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => copyToClipboard(newApiKey.key)}
                className="ml-2 flex gap-1"
              >
                <Copy className="h-4 w-4" /> 复制
              </Button>
            </div>
            <p className="text-amber-600 text-sm mt-4 flex items-center gap-1">
              <Clock className="h-4 w-4" /> 
              请务必立即复制此密钥。出于安全原因，之后将无法再次显示。
            </p>
          </CardContent>
          <CardFooter className="border-t bg-gray-50 flex justify-end">
            <Button variant="outline" onClick={() => setNewApiKey(null)}>
              完成
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* API Keys Table */}
      <Card>
        <CardHeader>
          <CardTitle>您的 API 密钥</CardTitle>
          <CardDescription>
            API 密钥可通过 API 完全访问您的账户。请妥善保管！
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="py-8 text-center text-gray-500">正在加载 API 密钥...</div>
          ) : apiKeys.length === 0 ? (
            <div className="py-8 text-center text-gray-500">
              未找到 API 密钥。请在上方创建新的 API 密钥。
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>密钥前缀</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead>最近使用</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <code className="text-xs bg-gray-100 p-1 rounded">{key.key_prefix}************</code>
                    </TableCell>
                    <TableCell>{formatDate(key.created_at)}</TableCell>
                    <TableCell>{key.last_used ? formatDate(key.last_used) : '从未使用'}</TableCell>
                    <TableCell>
                      {key.is_active ? (
                        <Badge variant="outline" className="bg-green-50 text-green-600 border-green-200">
                          <div className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" /> 已激活
                          </div>
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-gray-50 text-gray-600 border-gray-200">
                          <div className="flex items-center gap-1">
                            <XCircle className="h-3 w-3" /> 未激活
                          </div>
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              onClick={() => handleDeleteApiKey(key.id)}
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>删除 API 密钥</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>您确定吗？</AlertDialogTitle>
            <AlertDialogDescription>
              此操作无法撤销。这将永久删除该 API 密钥，任何使用该密钥的应用将无法再访问 API。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction 
              onClick={confirmDeleteApiKey}
              className="bg-red-600 hover:bg-red-700"
            >
              删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
} 