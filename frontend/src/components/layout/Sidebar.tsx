import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Home,
  Terminal,
  PlugZap,
  Key,
  Settings,
  HardDrive,
  HelpCircle,
  Users,
  Building2,
  Search,
  ChevronsLeft,
  ChevronsRight,
  BookOpen,
  PanelLeftClose,
  PanelLeftOpen,
  Brain,
} from "lucide-react"
import { Link, useLocation } from "react-router-dom"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { useAuth } from "@/context/AuthContext"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useState } from "react"

// App version - in a real app this would come from environment variables or build config
const APP_VERSION = "v1.0.0"

const sidebarItems = [
  { name: "Home", icon: Home, path: "/" },
  { name: "Documents", icon: Terminal, path: "/documents" },
  { name: "Knowledge Config", icon: Brain, path: "/knowledge-config" },
  { name: "Plugins", icon: PlugZap, path: "/plugins" },
  { name: "API Keys", icon: Key, path: "/api-keys" },
]

const bottomItems = [
  { name: "Settings", icon: Settings, path: "/settings" },
  { name: "Help", icon: HelpCircle, path: "/help" },
  { name: "Storage", icon: HardDrive, path: "/storage" },
]

export function Sidebar() {
  const location = useLocation()
  const { user, signOut } = useAuth()
  const [expanded, setExpanded] = useState(true)
  
  // Get user initials for avatar
  const getUserInitials = () => {
    if (!user?.email) return "U"
    return user.email.charAt(0).toUpperCase()
  }

  return (
    <div className={cn(
      "flex h-screen flex-col justify-between border-r bg-gray-50 text-gray-700 pb-4 transition-all duration-300 relative",
      expanded ? "w-56" : "w-16"
    )}>
      {/* Logo and Version */}
      <div className="flex items-center px-4 h-16 border-b border-gray-200 justify-between">
        {expanded ? (
          <>
            <div className="flex items-center">
              <span className="text-xl font-semibold">Simba</span>
              <span className="text-xs text-gray-500 ml-2">{APP_VERSION}</span>
            </div>
          </>
        ) : (
          <BookOpen className="h-6 w-6 mx-auto" />
        )}
        
        {/* Toggle Button - Integrated in header */}
        <Button 
          variant="ghost" 
          size="sm" 
          className="h-8 w-8 p-0 ml-2 hover:bg-gray-100 rounded-md"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeftOpen className="h-4 w-4" />}
        </Button>
      </div>
      
      {/* Search Bar */}
      {expanded && (
        <div className="px-4 pt-3 pb-2">
          <div className="relative flex items-center">
            <Search className="h-4 w-4 absolute left-3 text-gray-400" />
            <Input 
              className="pl-9 py-1 h-8 text-sm bg-white border-gray-200 text-gray-700 placeholder:text-gray-400"
              placeholder="Go to..."
            />
            <div className="absolute right-3 text-xs text-gray-500">⌘K</div>
          </div>
        </div>
      )}
      
      {/* Main Navigation */}
      <div className="flex-1 overflow-auto py-4">
        <div className={cn("space-y-1", expanded ? "px-3" : "px-2")}>
          {sidebarItems.map((item) => (
            <Link key={item.name} to={item.path}>
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "w-full justify-start text-gray-700 hover:text-gray-900 hover:bg-gray-100",
                  location.pathname === item.path && "bg-gray-100 text-gray-900 font-medium",
                  expanded ? "" : "justify-center px-2"
                )}
              >
                <item.icon className={cn("h-5 w-5", expanded ? "mr-3" : "")} />
                {expanded && item.name}
              </Button>
            </Link>
          ))}
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className={cn("space-y-1 border-t border-gray-200 pt-3 mt-auto", expanded ? "px-3" : "px-2")}>
        {bottomItems.map((item) => (
          <Link key={item.name} to={item.path}>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "w-full justify-start text-gray-700 hover:text-gray-900 hover:bg-gray-100",
                location.pathname === item.path && "bg-gray-100 text-gray-900 font-medium",
                expanded ? "" : "justify-center px-2"
              )}
            >
              <item.icon className={cn("h-5 w-5", expanded ? "mr-3" : "")} />
              {expanded && item.name}
            </Button>
          </Link>
        ))}
      </div>
      
      {/* User Section */}
      <div className={cn("pt-3 border-t border-gray-200 mt-2", expanded ? "px-3" : "px-2")}>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button 
              variant="ghost" 
              className={cn(
                "w-full hover:bg-gray-100 px-2", 
                expanded ? "justify-start" : "justify-center"
              )}
            >
              <Avatar className="h-8 w-8 bg-blue-100 text-blue-600 shrink-0">
                <AvatarFallback>{getUserInitials()}</AvatarFallback>
              </Avatar>
              {expanded && (
                <div className="flex flex-col items-start text-sm ml-2">
                  <span className="font-medium">{user?.email ? user.email.split('@')[0] : 'User'}</span>
                  <span className="text-xs text-gray-500">{user?.email || 'user@example.com'}</span>
                </div>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => signOut()}>
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}