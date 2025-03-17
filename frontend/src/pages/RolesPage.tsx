import React, { useEffect, useState } from 'react';
import { authAxios } from '@/lib/supabase';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/use-toast';

interface Role {
  id: number;
  name: string;
  description: string;
}

const testRoles = [
  { id: 1, name: 'admin', description: 'Full system access' },
  { id: 2, name: 'user', description: 'Standard user access' },
];

const RolesPage: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [bootstrapLoading, setBootstrapLoading] = useState(false);
  const [bootstrapSuccess, setBootstrapSuccess] = useState<string | null>(null);
  const [useTestData, setUseTestData] = useState(false);
  const [authInfo, setAuthInfo] = useState<any>(null);
  const { user } = useAuth();
  const { toast } = useToast();

  const fetchRoles = async () => {
    try {
      // Log the auth token for debugging
      const token = localStorage.getItem('accessToken');
      console.log('Auth token:', token ? `${token.substring(0, 15)}...` : 'No token');
      
      if (useTestData) {
        console.log('Using test data instead of API call');
        setRoles(testRoles);
        setError(null);
        return;
      }
      
      console.log('Fetching roles...');
      // Use /api prefix for consistent proxy routing
      const response = await authAxios.get('/api/roles');
      console.log('Roles response:', response.data);
      setRoles(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching roles:', err.response || err);
      console.error('Full error details:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        message: err.message
      });
      
      if (err.response?.status === 401) {
        toast({
          title: "Authentication Error",
          description: "Your session may have expired. Please try signing in again.",
          variant: "destructive"
        });
      }
      
      setError(err.response?.data?.detail || err.message || 'Failed to fetch roles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchRoles();
    } else {
      setLoading(false);
      setError('Please login to view roles');
    }
  }, [user]);

  const handleBootstrapAdmin = async () => {
    if (!user) return;
    
    setBootstrapLoading(true);
    setBootstrapSuccess(null);
    setError(null);
    
    if (useTestData) {
      // Simulate success for testing
      setTimeout(() => {
        console.log('Simulating bootstrap success with test data');
        setBootstrapSuccess(`User ${user.id} has been assigned the admin role`);
        setBootstrapLoading(false);
      }, 1000);
      return;
    }
    
    try {
      console.log(`Bootstrapping admin for user ID: ${user.id}`);
      // Use /api prefix for consistent proxy routing
      const response = await authAxios.post(`/api/roles/bootstrap/${user.id}`);
      console.log('Bootstrap response:', response.data);
      setBootstrapSuccess(response.data.message);
      
      // Refresh roles to see the changes
      await fetchRoles();
    } catch (err: any) {
      console.error('Error bootstrapping admin:', err.response || err);
      console.error('Full bootstrap error details:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        message: err.message
      });
      
      if (err.response?.status === 404) {
        toast({
          title: "Endpoint Not Found",
          description: "The bootstrap endpoint could not be found. The backend may not be properly configured.",
          variant: "destructive"
        });
      }
      
      setError(err.response?.data?.detail || err.message || 'Failed to bootstrap admin');
    } finally {
      setBootstrapLoading(false);
    }
  };

  // Function to check authentication status and details
  const checkAuth = () => {
    const token = localStorage.getItem('accessToken');
    const userId = localStorage.getItem('userId');
    const userEmail = localStorage.getItem('userEmail');
    
    setAuthInfo({
      hasToken: !!token,
      tokenPreview: token ? `${token.substring(0, 20)}...` : 'No token',
      userId,
      userEmail,
      userObject: user
    });
    
    toast({
      title: "Auth Status",
      description: token ? "Token found in localStorage" : "No token found",
      variant: token ? "default" : "destructive"
    });
  };

  if (!user) {
    return (
      <div className="container mx-auto p-4">
        <Alert>
          <AlertDescription>
            Please login to view roles
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle>Roles</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p>Loading roles...</p>
          ) : error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : bootstrapSuccess ? (
            <Alert className="mb-4">
              <AlertDescription>{bootstrapSuccess}</AlertDescription>
            </Alert>
          ) : null}
          
          {!loading && !error && (
            <>
              {roles.length === 0 ? (
                <p>No roles found</p>
              ) : (
                <ul className="space-y-2">
                  {roles.map(role => (
                    <li key={role.id} className="border p-3 rounded-md">
                      <strong>{role.name}</strong>: {role.description}
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
          
          <div className="mt-6 space-y-4">
            <div className="flex items-center">
              <input 
                type="checkbox" 
                id="useTestData" 
                checked={useTestData} 
                onChange={() => setUseTestData(!useTestData)}
                className="mr-2"
              />
              <label htmlFor="useTestData">Use test data (bypass API calls)</label>
            </div>
            
            <div className="border p-4 rounded-md">
              <h3 className="text-lg font-medium mb-2">Authentication Debugging</h3>
              <Button onClick={checkAuth} variant="outline" className="mb-2">Check Auth Status</Button>
              
              {authInfo && (
                <div className="bg-gray-100 p-3 rounded-md text-sm overflow-auto">
                  <pre>{JSON.stringify(authInfo, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button 
            onClick={handleBootstrapAdmin} 
            disabled={bootstrapLoading}
          >
            {bootstrapLoading ? 'Processing...' : 'Make Me Admin'}
          </Button>
          
          <Button 
            onClick={fetchRoles} 
            variant="outline"
          >
            Refresh Roles
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default RolesPage; 