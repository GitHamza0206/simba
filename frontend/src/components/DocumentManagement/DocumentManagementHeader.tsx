import React from 'react';
import { CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MoreVertical } from 'lucide-react';
import DocumentStats from '@/components/DocumentManagement/DocumentStats';
import { DocumentStatsType } from '@/types/document';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface DocumentManagementHeaderProps {
  stats: DocumentStatsType;
}

const DocumentManagementHeader: React.FC<DocumentManagementHeaderProps> = ({
  stats
}) => {
  return (
    <CardHeader>
      <div className="flex items-center justify-between">
        <CardTitle className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 py-2">Knowledge Management System</CardTitle>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              Configure System
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <DocumentStats 
        lastQueried={stats.lastQueried}
        totalQueries={stats.totalQueries}
        itemsIndexed={stats.itemsIndexed}
        createdAt={stats.createdAt}
      />
    </CardHeader>
  );
};

export default DocumentManagementHeader;