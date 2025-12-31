import { BarChart3, TrendingUp, Clock, ThumbsUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">
          Monitor performance and quality metrics.
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Avg. Response Time"
          value="1.2s"
          description="Target: < 2s"
          icon={Clock}
          trend="+5%"
          trendUp={false}
        />
        <MetricCard
          title="Resolution Rate"
          value="87%"
          description="Without human escalation"
          icon={TrendingUp}
          trend="+3%"
          trendUp={true}
        />
        <MetricCard
          title="User Satisfaction"
          value="4.6/5"
          description="Based on feedback"
          icon={ThumbsUp}
          trend="+0.2"
          trendUp={true}
        />
        <MetricCard
          title="Total Queries"
          value="2,847"
          description="This month"
          icon={BarChart3}
          trend="+12%"
          trendUp={true}
        />
      </div>

      {/* Charts placeholder */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Response Quality</CardTitle>
            <CardDescription>Evaluation scores over time</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <div className="flex h-full items-center justify-center text-muted-foreground">
              Chart will be displayed here
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Query Volume</CardTitle>
            <CardDescription>Conversations per day</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <div className="flex h-full items-center justify-center text-muted-foreground">
              Chart will be displayed here
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Eval Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Evaluation Metrics</CardTitle>
          <CardDescription>AI response quality breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <EvalMetric label="Relevance Score" value={0.94} />
            <EvalMetric label="Accuracy Score" value={0.91} />
            <EvalMetric label="Completeness Score" value={0.88} />
            <EvalMetric label="Citation Score" value={0.85} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  trendUp,
}: {
  title: string;
  value: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  trend: string;
  trendUp: boolean;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <div className="flex items-center gap-2 text-xs">
          <span className={trendUp ? "text-green-600" : "text-red-600"}>{trend}</span>
          <span className="text-muted-foreground">{description}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function EvalMetric({ label, value }: { label: string; value: number }) {
  const percentage = Math.round(value * 100);
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="font-medium">{percentage}%</span>
      </div>
      <div className="h-2 rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
