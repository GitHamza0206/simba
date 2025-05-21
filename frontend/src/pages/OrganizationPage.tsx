import React, { useEffect, useState } from 'react';
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
import { organizationApi, Organization, OrganizationMember, MemberRole } from '@/lib/api_services';

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
  const [activeTab, setActiveTab] = useState('general');
  
  const { user } = useAuth();
  const { toast } = useToast();

  // Fetch user's organizations
  const fetchOrganizations = async () => {
    try {
      setLoading(true);
      const data = await organizationApi.getOrganizations();
      setOrganizations(data);
      
      if (data.length > 0 && !selectedOrgId) {
        setSelectedOrgId(data[0].id);
        setSelectedOrgName(data[0].name);
      }
      
    } catch (err) {
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
      setLoading(true);
      const data = await organizationApi.getOrganizationMembers(selectedOrgId);
      setMembers(data);
    } catch (err) {
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
      const newOrg = await organizationApi.createOrganization({ name: newOrgName });
      await fetchOrganizations();
      setSelectedOrgId(newOrg.id);
      setSelectedOrgName(newOrg.name);
      setShowCreateForm(false);
      setNewOrgName('');
      
      toast({
        title: "Success",
        description: `Organization "${newOrgName}" created successfully`,
      });
    } catch (err) {
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
      await organizationApi.inviteMember(selectedOrgId, {
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
    } catch (err) {
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
      await organizationApi.updateMemberRole(selectedOrgId, memberId, { role: newRole });
      await fetchMembers();
      
      toast({
        title: "Success",
        description: "Member role updated successfully",
      });
    } catch (err) {
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
      await organizationApi.removeMember(selectedOrgId, memberId);
      await fetchMembers();
      
      toast({
        title: "Success",
        description: "Member removed successfully",
      });
    } catch (err) {
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
          <h1 className="text-2xl font-bold">组织管理</h1>
        </div>

        <div className="mb-6">
          <h2 className="text-lg font-medium mb-4">你的组织</h2>
          
          {error ? (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : (
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <p className="mb-4 text-gray-500">你还没有任何组织。请创建一个组织以开始使用。</p>
                  <Button onClick={() => setShowCreateForm(true)}>
                    <PlusIcon className="h-4 w-4 mr-2" /> 创建新组织
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
          
          {showCreateForm && (
            <Card className="mt-4">
              <CardHeader>
                <CardTitle>创建新组织</CardTitle>
                <CardDescription>为你的新组织输入一个名称</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">组织名称</Label>
                    <Input 
                      id="name" 
                      value={newOrgName} 
                      onChange={(e) => setNewOrgName(e.target.value)} 
                      placeholder="请输入组织名称"
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setShowCreateForm(false)}>取消</Button>
                <Button onClick={createOrganization}>创建组织</Button>
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
        <h1 className="text-2xl font-bold">组织设置</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <div className="border-b">
          <TabsList className="bg-transparent h-12">
            <TabsTrigger value="general" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              基本信息
            </TabsTrigger>
            <TabsTrigger value="members" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              成员
            </TabsTrigger>
            <TabsTrigger value="billing" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              账单
            </TabsTrigger>
            <TabsTrigger value="sso" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              单点登录
            </TabsTrigger>
            <TabsTrigger value="projects" className="data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-12">
              项目
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="general" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>组织详情</CardTitle>
              <CardDescription>管理你的组织信息</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="org-name">组织名称</Label>
                  <Input id="org-name" value={selectedOrgName || ''} readOnly />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="org-id">组织ID</Label>
                  <Input id="org-id" value={selectedOrgId || ''} readOnly />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>危险操作</CardTitle>
              <CardDescription>不可撤销的永久操作</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <Button variant="destructive">删除组织</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="members" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>成员</CardTitle>
                <CardDescription>管理你的组织成员</CardDescription>
              </div>
              <Button onClick={() => setShowInviteForm(true)} className="ml-auto">
                <PlusIcon className="h-4 w-4 mr-2" /> 邀请成员
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="py-10 text-center">正在加载成员...</div>
              ) : error ? (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>姓名</TableHead>
                      <TableHead>邮箱</TableHead>
                      <TableHead>角色</TableHead>
                      <TableHead>加入时间</TableHead>
                      <TableHead className="text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {members.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell className="font-medium">{member.name}</TableCell>
                        <TableCell>{member.email}</TableCell>
                        <TableCell>
                          <Select 
                            defaultValue={member.role}
                            onValueChange={(value: MemberRole) => updateMemberRole(member.id, value)}
                          >
                            <SelectTrigger className="w-24">
                              <SelectValue placeholder={member.role} />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="owner">拥有者</SelectItem>
                              <SelectItem value="admin">管理员</SelectItem>
                              <SelectItem value="member">成员</SelectItem>
                              <SelectItem value="viewer">访客</SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>{new Date(member.joined_at).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="text-red-500"
                            onClick={() => removeMember(member.id)}
                          >
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
                <CardTitle>邀请新成员</CardTitle>
                <CardDescription>发送邀请邮件加入该组织</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="email">邮箱地址</Label>
                    <Input 
                      id="email" 
                      type="email" 
                      value={inviteEmail} 
                      onChange={(e) => setInviteEmail(e.target.value)} 
                      placeholder="请输入邮箱地址"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="role">角色</Label>
                    <Select value={inviteRole} onValueChange={(value: MemberRole) => setInviteRole(value)}>
                      <SelectTrigger id="role">
                        <SelectValue placeholder="请选择角色" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">管理员</SelectItem>
                        <SelectItem value="member">成员</SelectItem>
                        <SelectItem value="viewer">访客</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setShowInviteForm(false)}>取消</Button>
                <Button onClick={inviteMember}>发送邀请</Button>
              </CardFooter>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="billing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>用量与账单</CardTitle>
              <CardDescription>管理你的订阅和账单信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex justify-between items-baseline mb-1">
                  <h3 className="text-sm font-medium text-gray-500">事件 / 近30天</h3>
                  <span className="text-sm font-medium">套餐上限: 50K</span>
                </div>
                <h2 className="text-3xl font-bold mb-1">0</h2>
                <div className="flex justify-between items-baseline mb-2">
                  <span className="text-sm">0.00%</span>
                </div>
                <Progress value={0} className="h-2" />
              </div>
              
              <div>
                <h3 className="text-sm font-medium mb-2">当前套餐: 体验版</h3>
                <div className="flex gap-2">
                  <Button>更改套餐</Button>
                  <Button variant="outline">对比套餐</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sso" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>单点登录</CardTitle>
              <CardDescription>为你的组织配置SSO</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="py-8 text-center text-gray-500">
                <p>单点登录仅在企业版套餐中提供。</p>
                <Button className="mt-4" variant="outline">升级到企业版</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="projects" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>项目</CardTitle>
              <CardDescription>管理你组织中的项目</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center py-4 border-b">
                <Button variant="outline" className="flex items-center">
                  查看项目 <ExternalLink className="ml-2 h-4 w-4" />
                </Button>
              </div>
              
              <div className="py-4">
                <h3 className="font-medium mb-2">最近的项目</h3>
                <p className="text-gray-500">尚未创建任何项目。</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default OrganizationPage; 