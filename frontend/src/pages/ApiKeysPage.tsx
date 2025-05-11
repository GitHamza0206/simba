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
        title: 'Error',
        description: 'Failed to load API keys',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async () => {
    if (!newKeyName.trim()) {
      toast({
        title: 'Error',
        description: 'Please provide a name for the API key',
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
        title: 'Success',
        description: 'API key created successfully',
      });
      
      // Clear input field
      setNewKeyName('');
    } catch (error) {
      console.error('Error creating API key:', error);
      toast({
        title: 'Error',
        description: 'Failed to create API key',
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
        title: 'Success',
        description: 'API key deleted successfully',
      });
    } catch (error) {
      console.error('Error deleting API key:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete API key',
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
          title: 'Copied',
          description: 'API key copied to clipboard',
        });
      })
      .catch((error) => {
        console.error('Failed to copy:', error);
        toast({
          title: 'Error',
          description: 'Failed to copy to clipboard',
          variant: 'destructive'
        });
      });
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMM d, yyyy HH:mm');
    } catch {
      return 'Invalid date';
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-screen-xl">
      <div className="flex flex-col mb-8">
        <h1 className="text-2xl font-bold">API Keys</h1>
        <p className="text-gray-500 mt-1">
          Create and manage API keys for programmatic access to your account.
        </p>
      </div>

      {/* New API Key Card */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Create New API Key</CardTitle>
          <CardDescription>
            Create a new API key to access the API programmatically. API keys are valid until revoked.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-grow">
              <Label htmlFor="new-key-name">API Key Name</Label>
              <Input
                id="new-key-name"
                placeholder="e.g., Development, Production, etc."
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
                {isCreatingKey ? 'Creating...' : 'Create API Key'}
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
              API Key Created Successfully
            </CardTitle>
            <CardDescription>
              Copy your API key now. You won't be able to see it again!
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
                <Copy className="h-4 w-4" /> Copy
              </Button>
            </div>
            <p className="text-amber-600 text-sm mt-4 flex items-center gap-1">
              <Clock className="h-4 w-4" /> 
              Make sure to copy this key now. For security reasons, it won't be displayed again.
            </p>
          </CardContent>
          <CardFooter className="border-t bg-gray-50 flex justify-end">
            <Button variant="outline" onClick={() => setNewApiKey(null)}>
              Done
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* API Keys Table */}
      <Card>
        <CardHeader>
          <CardTitle>Your API Keys</CardTitle>
          <CardDescription>
            API keys provide full access to your account via the API. Keep them secure!
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="py-8 text-center text-gray-500">Loading API keys...</div>
          ) : apiKeys.length === 0 ? (
            <div className="py-8 text-center text-gray-500">
              No API keys found. Create a new API key above.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Key Prefix</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
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
                    <TableCell>{key.last_used ? formatDate(key.last_used) : 'Never'}</TableCell>
                    <TableCell>
                      {key.is_active ? (
                        <Badge variant="outline" className="bg-green-50 text-green-600 border-green-200">
                          <div className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" /> Active
                          </div>
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-gray-50 text-gray-600 border-gray-200">
                          <div className="flex items-center gap-1">
                            <XCircle className="h-3 w-3" /> Inactive
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
                            <p>Delete API key</p>
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
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the API key
              and any applications using it will no longer be able to access the API.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={confirmDeleteApiKey}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
} 