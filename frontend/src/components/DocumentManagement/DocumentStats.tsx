import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Clock, Search, Database, Calendar } from 'lucide-react';

interface DocumentStatsProps {
  lastQueried: string;
  totalQueries: number;
  itemsIndexed: number;
  createdAt: string;
}

const DocumentStats: React.FC<DocumentStatsProps> = ({
  lastQueried,
  totalQueries,
  itemsIndexed,
  createdAt
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center space-x-4">
            <Clock className="w-4 h-4 text-gray-500" />
            <div>
              <p className="text-sm font-medium text-gray-500">上次查询时间</p>
              <p className="text-lg font-semibold">{lastQueried}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center space-x-4">
            <Search className="w-4 h-4 text-gray-500" />
            <div>
              <p className="text-sm font-medium text-gray-500">总查询次数</p>
              <p className="text-lg font-semibold">{totalQueries}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center space-x-4">
            <Database className="w-4 h-4 text-gray-500" />
            <div>
              <p className="text-sm font-medium text-gray-500">已索引条目</p>
              <p className="text-lg font-semibold">{itemsIndexed}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center space-x-4">
            <Calendar className="w-4 h-4 text-gray-500" />
            <div>
              <p className="text-sm font-medium text-gray-500">创建时间</p>
              <p className="text-lg font-semibold">{createdAt}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentStats;