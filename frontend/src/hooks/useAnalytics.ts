import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AnalyticsOverview, EvalMetrics, DailyStats } from "@/types/api";

const ANALYTICS_KEY = ["analytics"];

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "overview"],
    queryFn: () => api.get<AnalyticsOverview>("/api/v1/analytics/overview"),
  });
}

export function useEvalMetrics() {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "evals"],
    queryFn: () => api.get<EvalMetrics>("/api/v1/analytics/evals"),
  });
}

export function useDailyStats(days: number = 7) {
  return useQuery({
    queryKey: [...ANALYTICS_KEY, "daily", days],
    queryFn: () => api.get<DailyStats[]>(`/api/v1/analytics/daily?days=${days}`),
  });
}
