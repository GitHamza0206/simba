import React, { useState } from 'react';
import { Link, useNavigate, Outlet } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { ExternalLink } from 'lucide-react';

interface NavItem {
  name: string;
  path: string;
  external?: boolean;
}

const navItems: NavItem[] = [
  { name: 'General', path: '/settings' },
  { name: 'Members', path: '/settings/members' },
  { name: 'Billing', path: '/settings/billing' },
  { name: 'SSO', path: '/settings/sso' },
  { name: 'Projects', path: '/settings/projects' },
  { name: 'Roles', path: '/settings/roles' },
  { name: 'API Keys', path: '/settings/api-keys' },
];

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  // Get the current path to determine which nav item is active
  const currentPath = window.location.pathname;
  
  return (
    <div className="container mx-auto p-6 max-w-screen-xl">
      <div className="flex flex-col mb-8">
        <h1 className="text-2xl font-bold">Organization Settings</h1>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Left sidebar navigation */}
        <div className="w-full md:w-56">
          <nav className="flex flex-col space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.name}
                to={item.path}
                className={cn(
                  "px-3 py-2 text-sm font-medium rounded-md",
                  currentPath === item.path
                    ? "bg-gray-100 text-gray-900"
                    : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
                )}
              >
                <div className="flex items-center justify-between">
                  {item.name}
                  {item.external && <ExternalLink className="h-4 w-4 ml-2" />}
                </div>
              </Link>
            ))}
          </nav>
        </div>

        {/* Main content area */}
        <div className="flex-1">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default SettingsPage; 