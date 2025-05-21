import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Bell, ChevronDown } from "lucide-react"
import { useAuth } from "@/context/AuthContext"
import { useNavigate } from "react-router-dom"
import { Badge } from "@/components/ui/badge"

export function Navbar() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="border-b w-full bg-white">
      <div className="flex h-16 items-center px-4 w-full">
        <div className="flex items-center">
          {/* Organization Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex items-center gap-2 mr-4 h-10">
                组织
                <Badge variant="outline" className="ml-2 text-xs bg-gray-100">
                  爱好
                </Badge>
                <ChevronDown className="h-4 w-4 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-56">
              <DropdownMenuItem onClick={() => navigate('/organizations')}>
                管理组织
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