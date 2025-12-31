import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, MessageSquare, TrendingUp, Users } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your knowledge base and conversations.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Documents"
          value="24"
          description="+2 from last week"
          icon={FileText}
        />
        <StatsCard
          title="Conversations"
          value="1,234"
          description="+180 today"
          icon={MessageSquare}
        />
        <StatsCard
          title="Resolution Rate"
          value="89%"
          description="+2.5% from last month"
          icon={TrendingUp}
        />
        <StatsCard
          title="Active Users"
          value="573"
          description="Currently online"
          icon={Users}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Conversations</CardTitle>
            <CardDescription>Latest customer inquiries</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">No conversations yet.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Document Status</CardTitle>
            <CardDescription>Knowledge base overview</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatsCard({
  title,
  value,
  description,
  icon: Icon,
}: {
  title: string;
  value: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}
