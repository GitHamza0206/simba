import React from 'react';
import { CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from 'lucide-react';
import DocumentStats from '@/components/DocumentManagement/DocumentStats';
import { DocumentStatsType } from '@/types/document';

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