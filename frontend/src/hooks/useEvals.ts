import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";
import type {
  EvalListResponse,
  EvalItem,
  EvalItemCreate,
  EvalItemUpdate,
  GenerateQuestionsResponse,
} from "@/types/api";

const EVALS_KEY = ["evals"];

export function useEvals(skip: number = 0, limit: number = 50) {
  return useQuery({
    queryKey: [...EVALS_KEY, skip, limit],
    queryFn: () =>
      api.get<EvalListResponse>(`${API_ROUTES.EVALS}?skip=${skip}&limit=${limit}`),
  });
}

export function useEval(evalId: string) {
  return useQuery({
    queryKey: [...EVALS_KEY, evalId],
    queryFn: () => api.get<EvalItem>(`${API_ROUTES.EVALS}/${evalId}`),
    enabled: !!evalId,
  });
}

export function useCreateEval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EvalItemCreate) =>
      api.post<EvalItem>(API_ROUTES.EVALS, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVALS_KEY });
    },
  });
}

export function useUpdateEval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ evalId, data }: { evalId: string; data: EvalItemUpdate }) =>
      api.patch<EvalItem>(`${API_ROUTES.EVALS}/${evalId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVALS_KEY });
    },
  });
}

export function useDeleteEval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (evalId: string) =>
      api.delete(`${API_ROUTES.EVALS}/${evalId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVALS_KEY });
    },
  });
}

export function useGenerateQuestions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { collection_name: string; num_questions: number }) =>
      api.post<GenerateQuestionsResponse>(`${API_ROUTES.EVALS}/generate`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVALS_KEY });
    },
  });
}

export function useRunEval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { eval_id: string; collection_name: string }) =>
      api.post<EvalItem>(`${API_ROUTES.EVALS}/run`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: EVALS_KEY });
    },
  });
}
