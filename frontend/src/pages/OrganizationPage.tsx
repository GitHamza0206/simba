import React, { useEffect, useState } from 'react';
import { authAxios } from '@/lib/supabase';
import { Card, CardContent, CardHeader, CardTitle, CardFooter, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PlusIcon, TrashIcon } from 'lucide-react';

// Define organization and member interfaces
interface Organization {
  id: string;
  name: string;
  createdBy: string;
  createdAt: Date;
}

interface OrganizationMember {
  id: string;
  userId: string;
  name: string;
  email: string;
  role: MemberRole;
  joinedAt: Date;
}

type MemberRole = 'owner' | 'admin' | 'member' | 'viewer' | 'none';

// Test data for development
const testOrganizations: Organization[] = [
  {
    id: '1',
    name: 'Sample Organization',
    createdBy: 'current-user',
    createdAt: new Date(),
  }
];

const testMembers: OrganizationMember[] = [
  {
    id: '1',
    userId: 'current-user',
    name: 'Current User',
    email: 'user@example.com',
    role: 'owner',
    joinedAt: new Date(),
  },
  {
    id: '2',
    userId: 'user2',
    name: 'John Doe',
    email: 'john@example.com',
    role: 'admin',
    joinedAt: new Date(Date.now() - 24 * 60 * 60 * 1000),
  },
  {
    id: '3',
    userId: 'user3',
    name: 'Jane Smith',
    email: 'jane@example.com',
    role: 'member',
    joinedAt: new Date(Date.now() - 48 * 60 * 60 * 1000),
  }
];

const OrganizationPage: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<MemberRole>('member');
  const [useTestData, setUseTestData] = useState(false);
  
  const { user } = useAuth();
  const { toast } = useToast();

  // Fetch user's organizations
  const fetchOrganizations = async () => {
    try {
      if (useTestData) {
        setOrganizations(testOrganizations);
        if (!selectedOrgId && testOrganizations.length > 0) {
          setSelectedOrgId(testOrganizations[0].id);
        }
        return;
      }

      setLoading(true);
      const response = await authAxios.get('/api/organizations');
      setOrganizations(response.data);
      
      if (response.data.length > 0 && !selectedOrgId) {
        setSelectedOrgId(response.data[0].id);
      }
      
    } catch (err: any) {
      console.error('Error fetching organizations:', err);
      toast({
        title: "Error",
        description: "Failed to load your organizations",
        variant: "destructive"
      });
      setError('Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  // Fetch organization members
  const fetchMembers = async () => {
    if (!selectedOrgId) return;
    
    try {
      if (useTestData) {
        setMembers(testMembers);
        return;
      }

      setLoading(true);
      const response = await authAxios.get(`/api/organizations/${selectedOrgId}/members`);
      setMembers(response.data);
    } catch (err: any) {
      console.error('Error fetching members:', err);
      toast({
        title: "Error",
        description: "Failed to load organization members",
        variant: "destructive"
      });
      setError('Failed to load members');
    } finally {
      setLoading(false);
    }
  };

  // Create a new organization
  const createOrganization = async () => {
    if (!newOrgName.trim()) {
      toast({
        title: "Error",
        description: "Organization name cannot be empty",
        variant: "destructive"
      });
      return;
    }

    try {
      if (useTestData) {
        const newOrg: Organization = {
          id: Math.random().toString(36).substring(2, 9),
          name: newOrgName,
          createdBy: user?.id || 'current-user',
          createdAt: new Date()
        };
        
        setOrganizations([...organizations, newOrg]);
        setSelectedOrgId(newOrg.id);
        setShowCreateForm(false);
        setNewOrgName('');
        
        toast({
          title: "Success",
          description: `Organization "${newOrgName}" created successfully`,
        });
        return;
      }

      const response = await authAxios.post('/api/organizations', {
        name: newOrgName
      });
      
      await fetchOrganizations();
      setSelectedOrgId(response.data.id);
      setShowCreateForm(false);
      setNewOrgName('');
      
      toast({
        title: "Success",
        description: `Organization "${newOrgName}" created successfully`,
      });
    } catch (err: any) {
      console.error('Error creating organization:', err);
      toast({
        title: "Error",
        description: "Failed to create organization",
        variant: "destructive"
      });
    }
  };

  // Invite a new member
  const inviteMember = async () => {
    if (!selectedOrgId) return;
    
    if (!inviteEmail.trim() || !inviteEmail.includes('@')) {
      toast({
        title: "Error",
        description: "Please enter a valid email address",
        variant: "destructive"
      });
      return;
    }

    try {
      if (useTestData) {
        const newMember: OrganizationMember = {
          id: Math.random().toString(36).substring(2, 9),
          userId: Math.random().toString(36).substring(2, 9),
          name: inviteEmail.split('@')[0],
          email: inviteEmail,
          role: inviteRole,
          joinedAt: new Date()
        };
        
        setMembers([...members, newMember]);
        setInviteEmail('');
        setInviteRole('member');
        setShowInviteForm(false);
        
        toast({
          title: "Success",
          description: `Invitation sent to ${inviteEmail}`,
        });
        return;
      }

      await authAxios.post(`/api/organizations/${selectedOrgId}/invite`, {
        email: inviteEmail,
        role: inviteRole
      });
      
      await fetchMembers();
      setInviteEmail('');
      setInviteRole('member');
      setShowInviteForm(false);
      
      toast({
        title: "Success",
        description: `Invitation sent to ${inviteEmail}`,
      });
    } catch (err: any) {
      console.error('Error inviting member:', err);
      toast({
        title: "Error",
        description: "Failed to send invitation",
        variant: "destructive"
      });
    }
  };

  // Update member role
  const updateMemberRole = async (memberId: string, newRole: MemberRole) => {
    if (!selectedOrgId) return;
    
    try {
      if (useTestData) {
        setMembers(members.map(member => 
          member.id === memberId 
            ? { ...member, role: newRole } 
            : member
        ));
        
        toast({
          title: "Success",
          description: "Member role updated successfully",
        });
        return;
      }

      await authAxios.put(`/api/organizations/${selectedOrgId}/members/${memberId}`, {
        role: newRole
      });
      
      await fetchMembers();
      
      toast({
        title: "Success",
        description: "Member role updated successfully",
      });
    } catch (err: any) {
      console.error('Error updating member role:', err);
      toast({
        title: "Error",
        description: "Failed to update member role",
        variant: "destructive"
      });
    }
  };

  // Remove member
  const removeMember = async (memberId: string) => {
    if (!selectedOrgId) return;
    
    try {
      if (useTestData) {
        setMembers(members.filter(member => member.id !== memberId));
        
        toast({
          title: "Success",
          description: "Member removed successfully",
        });
        return;
      }

      await authAxios.delete(`/api/organizations/${selectedOrgId}/members/${memberId}`);
      
      await fetchMembers();
      
      toast({
        title: "Success",
        description: "Member removed successfully",
      });
    } catch (err: any) {
      console.error('Error removing member:', err);
      toast({
        title: "Error",
        description: "Failed to remove member",
        variant: "destructive"
      });
    }
  };

  // Load organizations on component mount
  useEffect(() => {
    if (user) {
      fetchOrganizations();
    }
  }, [user]);

  // Load members when selected organization changes
  useEffect(() => {
    if (selectedOrgId) {
      fetchMembers();
    }
  }, [selectedOrgId]);

  // Get selected organization
  const selectedOrg = selectedOrgId 
    ? organizations.find(org => org.id === selectedOrgId) 
    : null;

  // Check if current user is owner
  const isOwner = members.some(
    member => member.userId === (user?.id || 'current-user') && member.role === 'owner'
  );

  // Render organization selection
  const renderOrganizationSelector = () => (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-2">
        <Label htmlFor="organization-select">Your Organizations</Label>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setShowCreateForm(!showCreateForm)}
        >
          {showCreateForm ? 'Cancel' : 'Create New'}
        </Button>
      </div>
      
      {showCreateForm ? (
        <div className="flex gap-2 my-4">
          <Input
            placeholder="Organization Name"
            value={newOrgName}
            onChange={(e) => setNewOrgName(e.target.value)}
          />
          <Button onClick={createOrganization}>Create</Button>
        </div>
      ) : organizations.length > 0 ? (
        <Select 
          value={selectedOrgId || ''} 
          onValueChange={(value) => setSelectedOrgId(value)}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select an organization" />
          </SelectTrigger>
          <SelectContent>
            {organizations.map(org => (
              <SelectItem key={org.id} value={org.id}>
                {org.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : (
        <Alert>
          <AlertDescription>
            You don't have any organizations yet. Create one to get started.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );

  // Render member invite form
  const renderInviteForm = () => (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-medium">Invite Members</h3>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setShowInviteForm(!showInviteForm)}
        >
          {showInviteForm ? 'Cancel' : 'Add Member'}
        </Button>
      </div>
      
      {showInviteForm && (
        <div className="space-y-4 my-4 p-4 border rounded-md">
          <div>
            <Label htmlFor="invite-email">Email Address</Label>
            <Input
              id="invite-email"
              placeholder="user@example.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
            />
          </div>
          
          <div>
            <Label htmlFor="invite-role">Role</Label>
            <Select 
              value={inviteRole} 
              onValueChange={(value) => setInviteRole(value as MemberRole)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="member">Member</SelectItem>
                <SelectItem value="viewer">Viewer</SelectItem>
                <SelectItem value="none">None</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <Button onClick={inviteMember}>Send Invitation</Button>
        </div>
      )}
    </div>
  );

  // Render members table
  const renderMembersTable = () => (
    <div>
      <h3 className="text-lg font-medium mb-4">Organization Members</h3>
      
      {members.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name/Email</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Joined</TableHead>
              {isOwner && <TableHead>Actions</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {members.map(member => (
              <TableRow key={member.id}>
                <TableCell>
                  <div>
                    {member.name}
                    <div className="text-sm text-gray-500">{member.email}</div>
                  </div>
                </TableCell>
                <TableCell>
                  {member.role === 'owner' ? (
                    <span className="font-medium">{member.role}</span>
                  ) : isOwner ? (
                    <Select 
                      value={member.role} 
                      onValueChange={(value) => updateMemberRole(member.id, value as MemberRole)}
                      disabled={member.role === 'owner'}
                    >
                      <SelectTrigger className="w-[110px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="member">Member</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                        <SelectItem value="none">None</SelectItem>
                      </SelectContent>
                    </Select>
                  ) : (
                    <span>{member.role}</span>
                  )}
                </TableCell>
                <TableCell>
                  {new Date(member.joinedAt).toLocaleDateString()}
                </TableCell>
                {isOwner && (
                  <TableCell>
                    {member.role !== 'owner' && (
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => removeMember(member.id)}
                      >
                        <TrashIcon className="h-4 w-4" />
                      </Button>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : (
        <Alert>
          <AlertDescription>
            No members in this organization yet.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );

  if (!user) {
    return (
      <div className="container mx-auto p-4">
        <Alert>
          <AlertDescription>
            Please login to manage your organizations
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Organization Management</h1>
      
      {renderOrganizationSelector()}
      
      {selectedOrg && (
        <Card>
          <CardHeader>
            <CardTitle>{selectedOrg.name}</CardTitle>
            <CardDescription>
              Manage your organization members and their roles
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p>Loading...</p>
            ) : error ? (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : (
              <>
                {renderInviteForm()}
                {renderMembersTable()}
              </>
            )}
            
            <div className="mt-6">
              <div className="flex items-center mb-2">
                <input 
                  type="checkbox" 
                  id="useTestData" 
                  checked={useTestData} 
                  onChange={() => setUseTestData(!useTestData)}
                  className="mr-2"
                />
                <label htmlFor="useTestData" className="text-sm text-gray-600">
                  Use test data (for development)
                </label>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default OrganizationPage; 