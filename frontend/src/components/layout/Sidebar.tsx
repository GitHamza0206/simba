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
} from "lucide-react"
import { Link, useLocation } from "react-router-dom"

const sidebarItems = [
  { name: "Home", icon: Home, path: "/" },
  { name: "Organizations", icon: Building2, path: "/organizations" },
  { name: "Documents", icon: Terminal, path: "/documents" },
  { name: "Roles", icon: Users, path: "/roles" },
  { name: "Plugins", icon: PlugZap, path: "/plugins" },
  { name: "API Keys", icon: Key, path: "/api-keys" },
  { name: "Settings", icon: Settings, path: "/settings" },
]

const bottomItems = [
  { name: "Help", icon: HelpCircle, path: "/help" },
  { name: "Storage", icon: HardDrive, path: "/storage" },
]

export function Sidebar() {
  const location = useLocation()

  return (
    <div className="flex h-screen w-16 flex-col justify-between border-r bg-background pb-4">
      <div className="flex flex-col items-center space-y-2 pt-4">
        {sidebarItems.map((item) => (
          <Link key={item.name} to={item.path}>
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-12 w-12 rounded-xl",
                location.pathname === item.path && "bg-muted"
              )}
            >
              <item.icon className="h-6 w-6" />
              <span className="sr-only">{item.name}</span>
            </Button>
          </Link>
        ))}
      </div>

      <div className="flex flex-col items-center space-y-2">
        {bottomItems.map((item) => (
          <Link key={item.name} to={item.path}>
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-12 w-12 rounded-xl",
                location.pathname === item.path && "bg-muted"
              )}
            >
              <item.icon className="h-6 w-6" />
              <span className="sr-only">{item.name}</span>
            </Button>
          </Link>
        ))}
      </div>
    </div>
  )
}