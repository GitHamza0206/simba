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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PlusIcon, TrashIcon, ExternalLink } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

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
  const [selectedOrgName, setSelectedOrgName] = useState<string | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<MemberRole>('member');
  const [useTestData, setUseTestData] = useState(false);
  const [activeTab, setActiveTab] = useState('general');
  
  const { user } = useAuth();
  const { toast } = useToast();

  // Fetch user's organizations
  const fetchOrganizations = async () => {
    try {
      if (useTestData) {
        setOrganizations(testOrganizations);
        if (!selectedOrgId && testOrganizations.length > 0) {
          setSelectedOrgId(testOrganizations[0].id);
          setSelectedOrgName(testOrganizations[0].name);
        }
        return;
      }

      setLoading(true);
      const response = await authAxios.get('/api/organizations');
      setOrganizations(response.data);
      
      if (response.data.length > 0 && !selectedOrgId) {
        setSelectedOrgId(response.data[0].id);
        setSelectedOrgName(response.data[0].name);
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
        setSelectedOrgName(newOrg.name);
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
      setSelectedOrgName(response.data.name);
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

  // Load members when organization is selected
  useEffect(() => {
    if (selectedOrgId) {
      fetchMembers();
    }
  }, [selectedOrgId]);

  // Update organization name when selected org changes
  useEffect(() => {
    if (selectedOrgId) {
      const org = organizations.find(o => o.id === selectedOrgId);
      if (org) {
        setSelectedOrgName(org.name);
      }
    }
  }, [selectedOrgId, organizations]);

  if (organizations.length === 0 && !loading) {
    return (
      <div className="container mx-auto p-6 max-w-screen-xl">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold">Organization Management</h1>
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-medium mb-4">Your Organizations</h2>
          
          {error ? (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : (
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <p className="mb-4 text-gray-500">You don't have any organizations yet. Create one to get started.</p>
                  <Button onClick={() => setShowCreateForm(true)}>
                    <PlusIcon className="h-4 w-4 mr-2" /> Create New Organization
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
          
          {showCreateForm && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle>Create New Organization</CardTitle>
                <CardDescription>Enter a name for your new organization</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Organization Name</Label>
                    <Input 
                      id="name" 
                      value={newOrgName} 
                      onChange={(e) => setNewOrgName(e.target.value)} 
                      placeholder="Enter organization name"
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setShowCreateForm(false)}>Cancel</Button>
                <Button onClick={createOrganization}>Create Organization</Button>
              </CardFooter>
            </Card>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-screen-xl">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Organization Settings</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <div className="border-b">
          <TabsList className="bg-transparent h-12">
            <TabsTrigger value="general" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              General
            </TabsTrigger>
            <TabsTrigger value="members" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              Members
            </TabsTrigger>
            <TabsTrigger value="billing" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              Billing
            </TabsTrigger>
            <TabsTrigger value="sso" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              SSO
            </TabsTrigger>
            <TabsTrigger value="projects" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              Projects
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Organization Details</CardTitle>
              <CardDescription>Manage your organization information</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="org-name">Organization Name</Label>
                  <Input id="org-name" value={selectedOrgName || ''} readOnly />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="org-id">Organization ID</Label>
                  <Input id="org-id" value={selectedOrgId || ''} readOnly />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Danger Zone</CardTitle>
              <CardDescription>Permanent actions that cannot be undone</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <Button variant="destructive">Delete Organization</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="members" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Members</CardTitle>
                <CardDescription>Manage your organization members</CardDescription>
              </div>
              <Button onClick={() => setShowInviteForm(true)} className="ml-auto">
                <PlusIcon className="h-4 w-4 mr-2" /> Invite Member
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="py-10 text-center">Loading members...</div>
              ) : error ? (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Joined</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {members.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell className="font-medium">{member.name}</TableCell>
                        <TableCell>{member.email}</TableCell>
                        <TableCell>
                          <Select defaultValue={member.role}>
                            <SelectTrigger className="w-24">
                              <SelectValue placeholder={member.role} />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="owner">Owner</SelectItem>
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="member">Member</SelectItem>
                              <SelectItem value="viewer">Viewer</SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>{new Date(member.joinedAt).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="icon" className="text-red-500">
                            <TrashIcon className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {showInviteForm && (
            <Card>
              <CardHeader>
                <CardTitle>Invite New Member</CardTitle>
                <CardDescription>Send an invitation email to join this organization</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input 
                      id="email" 
                      type="email" 
                      value={inviteEmail} 
                      onChange={(e) => setInviteEmail(e.target.value)} 
                      placeholder="Enter email address"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="role">Role</Label>
                    <Select value={inviteRole} onValueChange={(value: MemberRole) => setInviteRole(value)}>
                      <SelectTrigger id="role">
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="member">Member</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setShowInviteForm(false)}>Cancel</Button>
                <Button onClick={inviteMember}>Send Invitation</Button>
              </CardFooter>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="billing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage & Billing</CardTitle>
              <CardDescription>Manage your subscription and billing details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex justify-between items-baseline mb-1">
                  <h3 className="text-sm font-medium text-gray-500">Events / last 30d</h3>
                  <span className="text-sm font-medium">Plan limit: 50K</span>
                </div>
                <h2 className="text-3xl font-bold mb-1">0</h2>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="text-sm">0.00%</span>
                </div>
                <Progress value={0} className="h-2" />
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">Current plan: Hobby</h3>
                <div className="flex gap-2">
                  <Button>Change plan</Button>
                  <Button variant="outline">Compare plans</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sso" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Single Sign-On</CardTitle>
              <CardDescription>Configure SSO for your organization</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="py-8 text-center text-gray-500">
                <p>SSO is only available on Enterprise plans.</p>
                <Button className="mt-4" variant="outline">Upgrade to Enterprise</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="projects" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Projects</CardTitle>
              <CardDescription>Manage the projects in your organization</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center py-4 border-b">
                <Button variant="outline" className="flex items-center">
                  View Projects <ExternalLink className="ml-2 h-4 w-4" />
                </Button>
              </div>
              
              <div className="py-4">
                <h3 className="font-medium mb-2">Recent Projects</h3>
                <p className="text-gray-500">No projects created yet.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default OrganizationPage; 