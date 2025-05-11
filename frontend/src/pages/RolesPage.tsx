import React, { useEffect, useState } from 'react';
import { authAxios } from '@/lib/supabase';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

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
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [userPermissions, setUserPermissions] = useState<Permission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const { toast } = useToast();

  const fetchRoles = async () => {
    try {
      // Check if we're in development mode without backend
      if (import.meta.env.DEV && !import.meta.env.VITE_API_URL) {
        console.log('Using test data in development mode');
        setRoles(testRoles);
        setPermissions(testPermissions);
        setError(null);
        return;
      }
      
      console.log('Fetching roles...');
      // Use /api prefix for consistent proxy routing
      const rolesResponse = await authAxios.get('/api/roles');
      console.log('Roles response:', rolesResponse.data);
      setRoles(rolesResponse.data);
      
      console.log('Fetching permissions...');
      const permissionsResponse = await authAxios.get('/api/roles/permissions');
      console.log('Permissions response:', permissionsResponse.data);
      setPermissions(permissionsResponse.data);

      if (user?.id) {
        console.log('Fetching user permissions...');
        const userPermissionsResponse = await authAxios.get(`/api/roles/user/${user.id}/permissions`);
        console.log('User permissions response:', userPermissionsResponse.data);
        setUserPermissions(userPermissionsResponse.data);
      }
      
      setError(null);
    } catch (err: any) {
      console.error('Error fetching roles or permissions:', err.response || err);
      
      if (err.response?.status === 401) {
        toast({
          title: "Authentication Error",
          description: "Your session may have expired. Please try signing in again.",
          variant: "destructive"
        });
      }
      
      setError(err.response?.data?.detail || err.message || 'Failed to fetch roles and permissions');
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