import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Bell, User, ChevronDown } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import { useNavigate } from "react-router-dom"
import { useState, useEffect } from "react"
import { authAxios } from "@/lib/supabase"
import { Badge } from "@/components/ui/badge"

interface Organization {
  id: string;
  name: string;
}

export function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch organizations when component mounts
    if (user) {
      fetchOrganizations();
    }
  }, [user]);

  const fetchOrganizations = async () => {
    try {
      setLoading(true);
      const response = await authAxios.get('/api/organizations');
      setOrganizations(response.data);
      
      // Set the first organization as selected if there is one
      if (response.data.length > 0) {
        setSelectedOrg(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching organizations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate('/auth/login');
  };

  const handleOrganizationSelect = (org: Organization) => {
    setSelectedOrg(org);
    // Here you would typically handle setting this as the active organization
    // and redirecting or updating app state
  };

  return (
    <div className="border-b w-full bg-white">
      <div className="flex h-16 items-center px-4 w-full">
        <div className="flex items-center">
          {/* Organization Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2 mr-4 h-10">
                {selectedOrg ? selectedOrg.name : "No Organization"}
                <Badge variant="outline" className="ml-2 text-xs bg-gray-100">
                  Hobby
                </Badge>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              {loading ? (
                <DropdownMenuItem disabled>Loading...</DropdownMenuItem>
              ) : organizations.length === 0 ? (
                <DropdownMenuItem disabled>No organizations</DropdownMenuItem>
              ) : (
                organizations.map((org) => (
                  <DropdownMenuItem 
                    key={org.id}
                    onClick={() => handleOrganizationSelect(org)}
                  >
                    {org.name}
                  </DropdownMenuItem>
                ))
              )}
              <DropdownMenuItem onClick={() => navigate('/organizations')}>
                Manage Organizations
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex items-center space-x-4 ml-auto">
          {user && (
            <>
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-600"></span>
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
} 