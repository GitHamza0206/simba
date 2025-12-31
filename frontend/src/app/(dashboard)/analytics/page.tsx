"use client";

import { BarChart3, TrendingUp, Clock, ThumbsUp, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnalyticsOverview, useEvalMetrics } from "@/hooks";

export default function AnalyticsPage() {
  const { data: overview, isLoading: overviewLoading } = useAnalyticsOverview();
  const { data: evalMetrics, isLoading: evalsLoading } = useEvalMetrics();

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
        {overviewLoading ? (
          <>
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
          </>
        ) : (
          <>
            <MetricCard
              title="Avg. Response Time"
              value={formatResponseTime(overview?.avg_response_time_ms.value ?? 0)}
              description="Target: < 2s"
              icon={Clock}
              trend={formatChange(overview?.avg_response_time_ms.change ?? 0)}
              trendUp={false}
            />
            <MetricCard
              title="Resolution Rate"
              value={formatPercent(overview?.resolution_rate.value ?? 0)}
              description="Without human escalation"
              icon={TrendingUp}
              trend={formatChange(overview?.resolution_rate.change ?? 0)}
              trendUp={(overview?.resolution_rate.change ?? 0) > 0}
            />
            <MetricCard
              title="User Satisfaction"
              value={formatSatisfaction(overview?.user_satisfaction.value ?? 0)}
              description="Based on feedback"
              icon={ThumbsUp}
              trend={formatChange(overview?.user_satisfaction.change ?? 0)}
              trendUp={(overview?.user_satisfaction.change ?? 0) > 0}
            />
            <MetricCard
              title="Total Conversations"
              value={formatNumber(overview?.total_conversations.value ?? 0)}
              description={`This ${overview?.total_conversations.period ?? "week"}`}
              icon={BarChart3}
              trend={formatChange(overview?.total_conversations.change ?? 0)}
              trendUp={(overview?.total_conversations.change ?? 0) > 0}
            />
          </>
        )}
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
          {evalsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-4">
              <EvalMetric label="Relevance Score" value={evalMetrics?.relevance_score ?? 0} />
              <EvalMetric label="Accuracy Score" value={evalMetrics?.accuracy_score ?? 0} />
              <EvalMetric label="Completeness Score" value={evalMetrics?.completeness_score ?? 0} />
              <EvalMetric label="Citation Score" value={evalMetrics?.citation_score ?? 0} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function formatResponseTime(ms: number): string {
  if (ms === 0) return "—";
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatPercent(value: number): string {
  if (value === 0) return "—";
  return `${Math.round(value * 100)}%`;
}

function formatSatisfaction(value: number): string {
  if (value === 0) return "—";
  return `${value.toFixed(1)}/5`;
}

function formatNumber(value: number): string {
  if (value === 0) return "—";
  return value.toLocaleString();
}

function formatChange(change: number): string {
  if (change === 0) return "—";
  const prefix = change > 0 ? "+" : "";
  return `${prefix}${Math.round(change)}%`;
}

function MetricCardSkeleton() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="h-4 w-4 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent>
        <div className="h-8 w-16 animate-pulse rounded bg-muted" />
        <div className="mt-2 h-4 w-32 animate-pulse rounded bg-muted" />
      </CardContent>
    </Card>
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
          <span className={trend === "—" ? "text-muted-foreground" : trendUp ? "text-green-600" : "text-red-600"}>
            {trend}
          </span>
          <span className="text-muted-foreground">{description}</span>
        </div>
      </CardContent>
    </Card>
  );
}

function EvalMetric({ label, value }: { label: string; value: number }) {
  const percentage = Math.round(value * 100);
  const displayValue = value === 0 ? "—" : `${percentage}%`;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span>{label}</span>
        <span className="font-medium">{displayValue}</span>
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
