import React, { useEffect, useState } from 'react';
// import instance from '@/lib/http/client'; // No longer directly used
import { rolesApi, Role, Permission } from '@/lib/rolesApi'; // Import the new API service and types
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AxiosError } from 'axios'; // For typing errors from the API service if needed directly here

// Local BackendErrorDetail for this component's specific error handling if needed
// This could also be imported from rolesApi if made exportable and common there.
interface BackendErrorDetail {
  detail?: string;
}

// Remove local definitions of Role and Permission, as they are imported from rolesApi.ts
/*
interface Role {
  id: number;
  name: string;
  description: string;
}

interface Permission {
  id: number;
  name: string;
  description: string;
}
*/

const testRoles = [
  { id: 1, name: 'admin', description: 'Full system access' },
  { id: 2, name: 'user', description: 'Standard user access' },
];

const testPermissions = [
  { id: 1, name: 'roles:read', description: 'Can view roles' },
  { id: 2, name: 'roles:write', description: 'Can create and update roles' },
  { id: 3, name: 'roles:delete', description: 'Can delete roles' },
];

const RolesPage: React.FC = () => {
  const [roles, setRoles] = useState<Role[]>([]); // Uses imported Role type
  const [permissions, setPermissions] = useState<Permission[]>([]); // Uses imported Permission type
  const [userPermissions, setUserPermissions] = useState<Permission[]>([]); // Uses imported Permission type
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const { toast } = useToast();

  const fetchRoles = async () => {
    setLoading(true);
    setError(null); // Clear previous errors
    try {
      // Check if we're in development mode without backend
      if (import.meta.env.DEV && !import.meta.env.VITE_API_URL) {
        console.log('Using test data in development mode for RolesPage');
        setRoles(testRoles);
        setPermissions(testPermissions);
        // Optionally set dummy user permissions or leave empty
        setUserPermissions(user?.id === '1' ? [testPermissions[0]] : []); // Example dummy user perm
        return;
      }
      
      console.log('Fetching roles using rolesApi...');
      const rolesData = await rolesApi.getRoles();
      console.log('Roles response:', rolesData);
      setRoles(rolesData);
      
      console.log('Fetching permissions using rolesApi...');
      const permissionsData = await rolesApi.getPermissions();
      console.log('Permissions response:', permissionsData);
      setPermissions(permissionsData);

      if (user?.id) {
        console.log('Fetching user permissions using rolesApi...');
        const userPermissionsData = await rolesApi.getUserPermissions(user.id);
        console.log('User permissions response:', userPermissionsData);
        setUserPermissions(userPermissionsData);
      }
      
    } catch (err: unknown) {
      console.error('Error in fetchRoles:', err);
      // The error thrown from rolesApi is already an Error instance with a message.
      // We can also check if it's an AxiosError if we need to access response status/data directly.
      let errorMessage = 'Failed to fetch roles and permissions';
      if (err instanceof Error) {
        errorMessage = err.message;
      }
      // Further check for AxiosError if specific status handling is needed
      const axiosError = err as AxiosError<BackendErrorDetail>; // Cast for potential Axios specific details
      if (axiosError.isAxiosError && axiosError.response?.status === 401) {
        toast({
          title: "Authentication Error",
          description: "Your session may have expired. Please try signing in again.",
          variant: "destructive"
        });
        // Use detail from AxiosError if available, otherwise the general error message
        errorMessage = axiosError.response?.data?.detail || errorMessage;
      } else if (axiosError.isAxiosError && axiosError.response?.data?.detail) {
         errorMessage = axiosError.response.data.detail;
      }

      setError(errorMessage);
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
      <Tabs defaultValue="roles">
        <TabsList className="mb-4">
          <TabsTrigger value="roles">Roles</TabsTrigger>
          <TabsTrigger value="permissions">All Permissions</TabsTrigger>
          <TabsTrigger value="user-permissions">My Permissions</TabsTrigger>
        </TabsList>
        
        <TabsContent value="roles">
          <Card>
            <CardHeader>
              <CardTitle>System Roles</CardTitle>
              <CardDescription>All roles defined in the system</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p>Loading roles...</p>
              ) : error ? (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
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
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="permissions">
          <Card>
            <CardHeader>
              <CardTitle>System Permissions</CardTitle>
              <CardDescription>All permissions available in the system</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p>Loading permissions...</p>
              ) : error ? (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : null}
              
              {!loading && !error && (
                <>
                  {permissions.length === 0 ? (
                    <p>No permissions found</p>
                  ) : (
                    <ul className="space-y-2">
                      {permissions.map(permission => (
                        <li key={permission.id} className="border p-3 rounded-md">
                          <strong>{permission.name}</strong>: {permission.description}
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="user-permissions">
          <Card>
            <CardHeader>
              <CardTitle>My Permissions</CardTitle>
              <CardDescription>Permissions assigned to your user account</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p>Loading your permissions...</p>
              ) : error ? (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : null}
              
              {!loading && !error && (
                <>
                  {userPermissions.length === 0 ? (
                    <p>You don't have any permissions assigned</p>
                  ) : (
                    <ul className="space-y-2">
                      {userPermissions.map(permission => (
                        <li key={permission.id} className="border p-3 rounded-md">
                          <strong>{permission.name}</strong>: {permission.description}
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default RolesPage; 