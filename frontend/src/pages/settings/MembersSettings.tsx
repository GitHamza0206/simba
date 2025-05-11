import React, { useState, useEffect } from 'react';
import { authAxios } from '@/lib/supabase';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ChevronFirst, ChevronLast, ChevronLeft, ChevronRight, Info, Loader2, PlusIcon, Trash2 } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';

interface ProjectMember {
  id: string;
  userId: string;
  name: string;
  email: string;
  organizationRole: string;
  projectRole: string;
}

interface Role {
  id: number;
  name: string;
  description: string;
}

const MembersSettings: React.FC = () => {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [columnsShown, setColumnsShown] = useState<number>(5);
  const [totalColumns] = useState<number>(6); // Using constant value
  const [rowsPerPage, setRowsPerPage] = useState<number>(10);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const { toast } = useToast();

  // Fetch current user and roles on component mount
  useEffect(() => {
    fetchCurrentUser();
  }, []);

  // Update total pages when members or rows per page changes
  useEffect(() => {
    setTotalPages(Math.max(1, Math.ceil(members.length / rowsPerPage)));
  }, [members, rowsPerPage]);

  const fetchCurrentUser = async () => {
    try {
      setLoading(true);
      const response = await authAxios.get('/auth/me');
      
      if (response.data) {
        const userData = response.data;
        console.log('User data:', userData);
        
        // Extract roles from user data
        if (userData.roles && Array.isArray(userData.roles)) {
          setRoles(userData.roles);
        }
        
        // Create member object from user data
        const currentMember: ProjectMember = {
          id: userData.id || '1',
          userId: userData.id || 'current-user',
          name: userData.user_metadata?.name || (userData.email ? userData.email.split('@')[0] : 'User'),
          email: userData.email || '',
          organizationRole: userData.roles && userData.roles.length > 0 ? userData.roles[0].name : 'Owner',
          projectRole: 'N/A on plan',
        };
        
        setMembers([currentMember]);
      }
    } catch (err: unknown) {
      console.error('Error fetching current user:', err);
      setError('Failed to load user data');
      
      // Fallback to test data if API call fails
      const fallbackMember: ProjectMember = {
        id: '1',
        userId: 'current-user',
        name: 'Hamza Zerouali',
        email: 'zeroualihamza0206@gmail.com',
        organizationRole: 'Owner',
        projectRole: 'N/A on plan',
      };
      
      // Default fallback roles
      setRoles([
        { id: 1, name: 'admin', description: 'Full system access with all permissions' },
        { id: 2, name: 'member', description: 'Standard access' },
        { id: 3, name: 'viewer', description: 'Read-only access' }
      ]);
      
      setMembers([fallbackMember]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMember = () => {
    toast({
      title: "Coming Soon",
      description: "Adding new members will be available in a future update",
    });
  };

  const getUserInitials = (name: string) => {
    if (!name) return "U";
    return name.charAt(0).toUpperCase();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2">Loading user data...</span>
      </div>
    );
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
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold">Project Members</h1>
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2">
                Columns <span className="text-sm text-gray-500">{columnsShown}/{totalColumns}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setColumnsShown(3)}>
                Show 3 columns
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setColumnsShown(4)}>
                Show 4 columns
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setColumnsShown(5)}>
                Show 5 columns
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setColumnsShown(6)}>
                Show all columns
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          
          <Button onClick={handleAddMember} className="flex items-center gap-2">
            <PlusIcon className="h-4 w-4" /> Add new member
          </Button>
        </div>
      </div>

      <Card className="border-t border-l border-r rounded-t-lg shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="bg-white hover:bg-white">
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead className="flex items-center gap-1">
                Organization Role
                <Info className="h-4 w-4 text-gray-400" />
              </TableHead>
              <TableHead className="flex items-center gap-1">
                Project Role
                <Info className="h-4 w-4 text-gray-400" />
              </TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {members.map(member => (
              <TableRow key={member.id} className="border-t hover:bg-gray-50">
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Avatar className="h-8 w-8 bg-blue-100 text-blue-600">
                      <AvatarFallback>{getUserInitials(member.name)}</AvatarFallback>
                    </Avatar>
                    <span>{member.name}</span>
                  </div>
                </TableCell>
                <TableCell>{member.email}</TableCell>
                <TableCell>
                  <Select defaultValue={member.organizationRole.toLowerCase()}>
                    <SelectTrigger className="w-40">
                      <SelectValue>{member.organizationRole}</SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {Array.isArray(roles) ? roles.map(role => (
                        <SelectItem key={role.id} value={role.name.toLowerCase()}>
                          {role.name}
                        </SelectItem>
                      )) : (
                        <SelectItem value="owner">Owner</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  <span className="text-gray-500">{member.projectRole}</span>
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon">
                    <Trash2 className="h-5 w-5 text-gray-500" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
      
      {/* Pagination */}
      <div className="flex items-center justify-between px-2">
        <div>
          <span className="text-sm text-gray-500">Rows per page</span>
          <Select value={rowsPerPage.toString()} onValueChange={(value) => setRowsPerPage(parseInt(value))}>
            <SelectTrigger className="w-20 ml-2">
              <SelectValue>{rowsPerPage}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="5">5</SelectItem>
              <SelectItem value="10">10</SelectItem>
              <SelectItem value="20">20</SelectItem>
              <SelectItem value="50">50</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            Page
            <Input 
              className="w-12 mx-2 inline-block"
              value={currentPage}
              onChange={(e) => {
                const value = parseInt(e.target.value);
                if (!isNaN(value) && value > 0 && value <= totalPages) {
                  setCurrentPage(value);
                }
              }}
            />
            of {totalPages}
          </span>
          
          <div className="flex items-center gap-1">
            <Button variant="outline" size="icon" disabled={currentPage === 1}
              onClick={() => setCurrentPage(1)}>
              <ChevronFirst className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}>
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(totalPages)}>
              <ChevronLast className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MembersSettings; 