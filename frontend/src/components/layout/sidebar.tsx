"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ROUTES } from "@/lib/constants";
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  BarChart3,
  ClipboardCheck,
  Rocket,
  HelpCircle,
  Play,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: ROUTES.HOME, icon: LayoutDashboard },
  { name: "Playground", href: ROUTES.PLAYGROUND, icon: Play },
  { name: "Documents", href: ROUTES.DOCUMENTS, icon: FileText },
  { name: "Conversations", href: ROUTES.CONVERSATIONS, icon: MessageSquare },
  { name: "Analytics", href: ROUTES.ANALYTICS, icon: BarChart3 },
  { name: "Evals", href: ROUTES.EVALS, icon: ClipboardCheck },
  { name: "Deploy", href: ROUTES.DEPLOY, icon: Rocket },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 flex-col border-r bg-card">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <span className="text-lg font-bold">S</span>
        </div>
        <span className="text-xl font-semibold">Simba</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t p-4">
        <Link
          href="https://github.com/GitHamza0206/simba"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <HelpCircle className="h-5 w-5" />
          Help & Docs
        </Link>
      </div>
    </aside>
  );
}
