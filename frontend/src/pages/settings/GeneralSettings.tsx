import React, { useState, useEffect } from 'react';
import { authAxios } from '@/lib/supabase';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface Organization {
  id: string;
  name: string;
}

const GeneralSettings: React.FC = () => {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [orgName, setOrgName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    fetchOrganization();
  }, []);

  const fetchOrganization = async () => {
    try {
      setLoading(true);
      // For development, use a sample organization
      if (import.meta.env.DEV && !import.meta.env.VITE_API_URL) {
        setOrganization({ id: 'cm8d8jb2u0ncad07rseshkov', name: 'atlanta' });
        setOrgName('atlanta');
        setMetadata(JSON.stringify({ id: 'cm8d8jb2u0ncad07rseshkov', name: 'atlanta' }, null, 2));
        return; // Return early in dev mode without API URL
      }
      
      // const response = await authAxios.get('/api/organizations/current');
      // setOrganization(response.data);
      // setOrgName(response.data.name);
      // setMetadata(JSON.stringify(response.data, null, 2));
      
      // If API is commented out, provide some default or indicate error more clearly
      // For now, we'll let the error state handle it if not in dev mode.
      if (!(import.meta.env.DEV && !import.meta.env.VITE_API_URL)) {
         setError('Backend API calls are currently disabled.'); 
         // Optionally set some default state if needed
         // setOrganization(null);
         // setOrgName('');
         // setMetadata('{}');
      }

    } catch (err: any) {
      console.error('Error fetching organization:', err);
      // Keep existing error handling
      setError('Failed to load organization details');
    } finally {
      setLoading(false); // Ensure loading state is always turned off
    }
  };

  const handleSaveOrgName = async () => {
    if (!orgName.trim()) {
      toast({
        title: "Error",
        description: "Organization name cannot be empty",
        variant: "destructive"
      });
      return;
    }

    try {
      // For development, just show success
      if (import.meta.env.DEV && !import.meta.env.VITE_API_URL) {
        setOrganization(prev => prev ? { ...prev, name: orgName } : null);
        toast({
          title: "Success",
          description: "Organization name updated successfully (Dev Mode)",
        });
        return; // Return early in dev mode without API URL
      }
      
      // await authAxios.put(`/api/organizations/${organization?.id}`, {
      //   name: orgName
      // });
      
      toast({
        title: "Info",
        description: "Organization name update is currently disabled.",
      });
      
      // fetchOrganization(); // No need to refetch if the PUT is disabled
    } catch (err: any) {
      console.error('Error updating organization name:', err);
      toast({
        title: "Error",
        description: "Failed to update organization name",
        variant: "destructive"
      });
    }
  };

  if (loading) {
    return <div>Loading organization details...</div>;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Organization Name</CardTitle>
          <CardDescription>Change the name of your organization</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <p className="text-sm text-gray-500 mb-4">
              Your Organization is currently named "<span className="font-medium">{organization?.name}</span>".
            </p>
            <Input 
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              className="max-w-md mb-4"
            />
            <Button onClick={handleSaveOrgName}>Save</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Debug Information</CardTitle>
          <CardDescription>Metadata for this organization</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="bg-gray-50 p-4 rounded-md overflow-auto text-xs">
            {`{\n  name: "${organization?.name}",\n  id: "${organization?.id}"\n}`}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Danger Zone</CardTitle>
          <CardDescription>Permanent actions that cannot be undone</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="font-medium mb-1">Delete this organization</h3>
              <p className="text-sm text-gray-500 mb-2">Once you delete an organization, there is no going back. Please be certain.</p>
              <Button variant="destructive">Delete Organization</Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GeneralSettings; 