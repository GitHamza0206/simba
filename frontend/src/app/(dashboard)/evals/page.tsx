"use client";

import { useState, useMemo } from "react";
import {
  ClipboardCheck,
  Plus,
  Trash2,
  Loader2,
  Play,
  Sparkles,
  Edit2,
  Check,
  X,
  ChevronDown,
  ChevronRight,
  Clock,
  Download,
  FileJson,
  FileSpreadsheet,
  Terminal,
  PlayCircle,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Target,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useEvals,
  useCreateEval,
  useUpdateEval,
  useDeleteEval,
  useGenerateQuestions,
  useRunEval,
  useRunAllEvals,
  useCollections,
} from "@/hooks";
import type { EvalItem } from "@/types/api";

const ERROR_CATEGORIES = [
  { value: "", label: "None" },
  { value: "wrong_source", label: "Wrong Source" },
  { value: "hallucination", label: "Hallucination" },
  { value: "incomplete", label: "Incomplete" },
  { value: "irrelevant", label: "Irrelevant" },
  { value: "outdated", label: "Outdated Info" },
];

function formatLatency(ms: number | null): string {
  if (ms === null) return "—";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatPercent(value: number | null): string {
  if (value === null) return "—";
  return `${Math.round(value * 100)}%`;
}

function formatScore(value: number | null): string {
  if (value === null) return "—";
  return value.toFixed(2);
}

function ScoreBadge({ value, label }: { value: number | null; label: string }) {
  if (value === null) return <span className="text-xs text-muted-foreground">—</span>;

  let colorClass = "bg-red-100 text-red-700";
  if (value >= 0.7) colorClass = "bg-green-100 text-green-700";
  else if (value >= 0.5) colorClass = "bg-yellow-100 text-yellow-700";

  return (
    <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${colorClass}`} title={label}>
      {formatScore(value)}
    </span>
  );
}

function PassBadge({ passed }: { passed: boolean | null }) {
  if (passed === null) return <span className="text-xs text-muted-foreground">—</span>;

  return passed ? (
    <Badge variant="outline" className="border-green-500 bg-green-50 text-green-700">
      <CheckCircle2 className="mr-1 h-3 w-3" />
      Pass
    </Badge>
  ) : (
    <Badge variant="outline" className="border-red-500 bg-red-50 text-red-700">
      <XCircle className="mr-1 h-3 w-3" />
      Fail
    </Badge>
  );
}

function EvalRow({
  evalItem,
  onDelete,
  onRun,
  onUpdateComment,
  onUpdateErrorCategory,
  isDeleting,
  isRunning,
}: {
  evalItem: EvalItem;
  onDelete: () => void;
  onRun: () => void;
  onUpdateComment: (comment: string) => void;
  onUpdateErrorCategory: (category: string) => void;
  isDeleting: boolean;
  isRunning: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const [editingComment, setEditingComment] = useState(false);
  const [commentValue, setCommentValue] = useState(evalItem.comment || "");

  const handleSaveComment = () => {
    onUpdateComment(commentValue);
    setEditingComment(false);
  };

  const handleCancelComment = () => {
    setCommentValue(evalItem.comment || "");
    setEditingComment(false);
  };

  return (
    <>
      <tr className="border-b last:border-0 hover:bg-muted/50">
        <td className="p-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-2 text-left"
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            <span className="max-w-[200px] truncate font-medium">{evalItem.question}</span>
          </button>
        </td>
        <td className="p-3">
          <PassBadge passed={evalItem.passed} />
        </td>
        <td className="p-3">
          <div className="flex gap-1">
            <ScoreBadge value={evalItem.relevance_score} label="Relevance" />
          </div>
        </td>
        <td className="p-3">
          <div className="flex gap-1">
            <ScoreBadge value={evalItem.faithfulness_score} label="Faithfulness" />
          </div>
        </td>
        <td className="p-3">
          <span className="text-xs">{formatPercent(evalItem.retrieval_precision)}</span>
        </td>
        <td className="p-3">
          <span className="text-xs">{formatPercent(evalItem.retrieval_recall)}</span>
        </td>
        <td className="p-3">
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatLatency(evalItem.latency_ms)}
          </div>
        </td>
        <td className="p-3">
          {evalItem.error_category ? (
            <Badge variant="outline" className="text-xs border-orange-500 text-orange-600">
              {evalItem.error_category}
            </Badge>
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          )}
        </td>
        <td className="p-3">
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={onRun}
              disabled={isRunning}
              title="Run evaluation"
            >
              {isRunning ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onDelete}
              disabled={isDeleting}
              className="text-red-600 hover:text-red-700"
              title="Delete"
            >
              {isDeleting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </Button>
          </div>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-muted/30">
          <td colSpan={9} className="p-4">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium">Full Question</h4>
                  <p className="mt-1 text-sm">{evalItem.question}</p>
                </div>
                {evalItem.response && (
                  <div>
                    <h4 className="text-sm font-medium">Response</h4>
                    <p className="mt-1 whitespace-pre-wrap text-sm">{evalItem.response}</p>
                  </div>
                )}
                {evalItem.sources && evalItem.sources.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium">Sources Retrieved</h4>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {evalItem.sources.map((source, i) => (
                        <Badge key={i} variant="secondary">
                          {source}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {evalItem.sources_groundtruth && evalItem.sources_groundtruth.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium">Expected Sources (Groundtruth)</h4>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {evalItem.sources_groundtruth.map((source, i) => (
                        <Badge key={i} variant="outline" className="border-green-500 text-green-600">
                          {source}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {evalItem.answer_groundtruth && (
                  <div>
                    <h4 className="text-sm font-medium">Expected Answer (Groundtruth)</h4>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground bg-green-50 p-2 rounded border border-green-200">
                      {evalItem.answer_groundtruth}
                    </p>
                  </div>
                )}
              </div>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium">Comment</h4>
                  {editingComment ? (
                    <div className="mt-1 flex items-center gap-2">
                      <input
                        type="text"
                        value={commentValue}
                        onChange={(e) => setCommentValue(e.target.value)}
                        className="h-8 flex-1 rounded border bg-background px-2 text-sm"
                        autoFocus
                      />
                      <Button variant="ghost" size="sm" onClick={handleSaveComment}>
                        <Check className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={handleCancelComment}>
                        <X className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  ) : (
                    <div className="mt-1 flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">
                        {evalItem.comment || "No comment"}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setEditingComment(true)}
                        className="h-6 w-6 p-0"
                      >
                        <Edit2 className="h-3 w-3" />
                      </Button>
                    </div>
                  )}
                </div>
                <div>
                  <h4 className="text-sm font-medium">Error Category</h4>
                  <select
                    value={evalItem.error_category || ""}
                    onChange={(e) => onUpdateErrorCategory(e.target.value)}
                    className="mt-1 h-8 rounded border bg-background px-2 text-sm"
                  >
                    {ERROR_CATEGORIES.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Relevance:</span>{" "}
                    <span className="font-medium">{formatScore(evalItem.relevance_score)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Faithfulness:</span>{" "}
                    <span className="font-medium">{formatScore(evalItem.faithfulness_score)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Precision:</span>{" "}
                    <span className="font-medium">{formatPercent(evalItem.retrieval_precision)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Recall:</span>{" "}
                    <span className="font-medium">{formatPercent(evalItem.retrieval_recall)}</span>
                  </div>
                </div>
                {evalItem.conversation_history && (
                  <div>
                    <h4 className="text-sm font-medium">Conversation History</h4>
                    <pre className="mt-1 max-h-32 overflow-auto rounded bg-muted p-2 text-xs">
                      {evalItem.conversation_history}
                    </pre>
                  </div>
                )}
                <div className="text-xs text-muted-foreground">
                  Created: {formatDate(evalItem.created_at)}
                  {evalItem.updated_at !== evalItem.created_at && (
                    <> | Updated: {formatDate(evalItem.updated_at)}</>
                  )}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function StatsCards({ evals }: { evals: EvalItem[] }) {
  const stats = useMemo(() => {
    const withResults = evals.filter((e) => e.response !== null);
    const passed = withResults.filter((e) => e.passed === true).length;
    const failed = withResults.filter((e) => e.passed === false).length;
    const passRate = withResults.length > 0 ? passed / withResults.length : null;

    const avgLatency = withResults.length > 0
      ? withResults.reduce((acc, e) => acc + (e.latency_ms || 0), 0) / withResults.length
      : null;

    const avgRelevance = withResults.filter((e) => e.relevance_score !== null).length > 0
      ? withResults.reduce((acc, e) => acc + (e.relevance_score || 0), 0) /
        withResults.filter((e) => e.relevance_score !== null).length
      : null;

    const avgFaithfulness = withResults.filter((e) => e.faithfulness_score !== null).length > 0
      ? withResults.reduce((acc, e) => acc + (e.faithfulness_score || 0), 0) /
        withResults.filter((e) => e.faithfulness_score !== null).length
      : null;

    return { total: evals.length, withResults: withResults.length, passed, failed, passRate, avgLatency, avgRelevance, avgFaithfulness };
  }, [evals]);

  return (
    <div className="grid gap-4 md:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Pass Rate</CardTitle>
          <Target className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {stats.passRate !== null ? `${Math.round(stats.passRate * 100)}%` : "—"}
          </div>
          <p className="text-xs text-muted-foreground">
            {stats.passed} passed, {stats.failed} failed
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Relevance</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatScore(stats.avgRelevance)}</div>
          <p className="text-xs text-muted-foreground">Response relevance to question</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Faithfulness</CardTitle>
          <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatScore(stats.avgFaithfulness)}</div>
          <p className="text-xs text-muted-foreground">Grounded in context</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatLatency(stats.avgLatency)}</div>
          <p className="text-xs text-muted-foreground">{stats.withResults} evaluated</p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function EvalsPage() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [newQuestion, setNewQuestion] = useState("");
  const [newGroundtruth, setNewGroundtruth] = useState("");
  const [newAnswerGroundtruth, setNewAnswerGroundtruth] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [selectedCollection, setSelectedCollection] = useState("default");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [showClaudeCodeModal, setShowClaudeCodeModal] = useState(false);
  const [claudeCodePrompt, setClaudeCodePrompt] = useState("");
  const [copied, setCopied] = useState(false);

  const { data, isLoading } = useEvals();
  const { data: collectionsData } = useCollections();
  const createMutation = useCreateEval();
  const updateMutation = useUpdateEval();
  const deleteMutation = useDeleteEval();
  const generateMutation = useGenerateQuestions();
  const runMutation = useRunEval();
  const runAllMutation = useRunAllEvals();

  const evals = data?.items ?? [];
  const collections = collectionsData?.items ?? [];

  const handleCreate = async () => {
    if (!newQuestion.trim()) return;

    await createMutation.mutateAsync({
      question: newQuestion,
      sources_groundtruth: newGroundtruth ? newGroundtruth.split(",").map((s) => s.trim()) : null,
      answer_groundtruth: newAnswerGroundtruth || null,
    });
    setNewQuestion("");
    setNewGroundtruth("");
    setNewAnswerGroundtruth("");
    setShowAddModal(false);
  };

  const handleDelete = async (evalItem: EvalItem) => {
    if (!confirm("Delete this eval item? This cannot be undone.")) return;

    setDeletingId(evalItem.id);
    try {
      await deleteMutation.mutateAsync(evalItem.id);
    } finally {
      setDeletingId(null);
    }
  };

  const handleRun = async (evalItem: EvalItem) => {
    setRunningId(evalItem.id);
    try {
      await runMutation.mutateAsync({
        eval_id: evalItem.id,
        collection_name: selectedCollection,
      });
    } finally {
      setRunningId(null);
    }
  };

  const handleRunAll = async () => {
    await runAllMutation.mutateAsync({
      collection_name: selectedCollection,
    });
  };

  const handleUpdateComment = async (evalId: string, comment: string) => {
    await updateMutation.mutateAsync({
      evalId,
      data: { comment },
    });
  };

  const handleUpdateErrorCategory = async (evalId: string, errorCategory: string) => {
    await updateMutation.mutateAsync({
      evalId,
      data: { error_category: errorCategory || null },
    });
  };

  const handleGenerate = async () => {
    const result = await generateMutation.mutateAsync({
      collection_name: selectedCollection,
      num_questions: numQuestions,
    });

    for (const q of result.questions) {
      await createMutation.mutateAsync({
        question: q.question,
        sources_groundtruth: q.source_documents,
        answer_groundtruth: q.answer_groundtruth,
      });
    }

    setShowGenerateModal(false);
  };

  const getExportData = () => {
    return {
      evaluation_results: evals.map((e) => ({
        id: e.id,
        question: e.question,
        response: e.response,
        sources: e.sources,
        sources_groundtruth: e.sources_groundtruth,
        answer_groundtruth: e.answer_groundtruth,
        comment: e.comment,
        latency_ms: e.latency_ms,
        retrieval_precision: e.retrieval_precision,
        retrieval_recall: e.retrieval_recall,
        relevance_score: e.relevance_score,
        faithfulness_score: e.faithfulness_score,
        passed: e.passed,
        error_category: e.error_category,
      })),
      exported_at: new Date().toISOString(),
      collection: selectedCollection,
    };
  };

  const exportToJson = () => {
    const data = getExportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `evals-${selectedCollection}-${new Date().toISOString().split("T")[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const exportToCsv = () => {
    const headers = [
      "id", "question", "response", "sources", "sources_groundtruth",
      "retrieval_precision", "retrieval_recall", "relevance_score",
      "faithfulness_score", "passed", "error_category", "comment", "latency_ms"
    ];
    const rows = evals.map((e) => [
      e.id,
      `"${(e.question || "").replace(/"/g, '""')}"`,
      `"${(e.response || "").replace(/"/g, '""')}"`,
      `"${(e.sources || []).join("; ")}"`,
      `"${(e.sources_groundtruth || []).join("; ")}"`,
      e.retrieval_precision ?? "",
      e.retrieval_recall ?? "",
      e.relevance_score ?? "",
      e.faithfulness_score ?? "",
      e.passed ?? "",
      e.error_category || "",
      `"${(e.comment || "").replace(/"/g, '""')}"`,
      e.latency_ms ?? "",
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `evals-${selectedCollection}-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    setShowExportMenu(false);
  };

  const exportToClaudeCode = () => {
    const data = getExportData();
    const prompt = `/improve-simba ${JSON.stringify(data, null, 2)}`;
    setClaudeCodePrompt(prompt);
    setShowClaudeCodeModal(true);
    setShowExportMenu(false);
  };

  const copyClaudeCodePrompt = () => {
    navigator.clipboard.writeText(claudeCodePrompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const pendingEvals = evals.filter((e) => e.response === null).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Evaluations</h1>
          <p className="text-muted-foreground">
            Measure and track customer service quality.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Button
              variant="outline"
              onClick={() => setShowExportMenu(!showExportMenu)}
            >
              <Download className="mr-2 h-4 w-4" />
              Export
              <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
            {showExportMenu && (
              <div className="absolute right-0 top-full z-10 mt-1 w-48 rounded-md border bg-background shadow-lg">
                <button
                  onClick={exportToJson}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-muted"
                >
                  <FileJson className="h-4 w-4" />
                  Export as JSON
                </button>
                <button
                  onClick={exportToCsv}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-muted"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  Export as CSV
                </button>
                <button
                  onClick={exportToClaudeCode}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-muted"
                >
                  <Terminal className="h-4 w-4" />
                  Export to Claude Code
                </button>
              </div>
            )}
          </div>
          <select
            value={selectedCollection}
            onChange={(e) => setSelectedCollection(e.target.value)}
            className="h-9 rounded-md border bg-background px-3 text-sm"
          >
            <option value="default">default</option>
            {collections.map((c) => (
              <option key={c.id} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
          {pendingEvals > 0 && (
            <Button
              variant="outline"
              onClick={handleRunAll}
              disabled={runAllMutation.isPending}
            >
              {runAllMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <PlayCircle className="mr-2 h-4 w-4" />
              )}
              Run All ({pendingEvals})
            </Button>
          )}
          <Button variant="outline" onClick={() => setShowGenerateModal(true)}>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate
          </Button>
          <Button onClick={() => setShowAddModal(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Eval
          </Button>
        </div>
      </div>

      <StatsCards evals={evals} />

      <Card>
        <CardHeader>
          <CardTitle>Evaluation Items</CardTitle>
          <CardDescription>
            {isLoading ? "Loading..." : `${evals.length} evaluation(s)`}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : evals.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                <ClipboardCheck className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mt-4 text-lg font-semibold">No evaluations yet</h3>
              <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
                Add evaluation questions manually or generate them from your documents to measure
                response quality.
              </p>
              <div className="mt-4 flex gap-2">
                <Button variant="outline" onClick={() => setShowGenerateModal(true)}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Generate from Docs
                </Button>
                <Button onClick={() => setShowAddModal(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Manually
                </Button>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="p-3 text-left font-medium">Question</th>
                    <th className="p-3 text-left font-medium">Status</th>
                    <th className="p-3 text-left font-medium">Relevance</th>
                    <th className="p-3 text-left font-medium">Faithful</th>
                    <th className="p-3 text-left font-medium">Precision</th>
                    <th className="p-3 text-left font-medium">Recall</th>
                    <th className="p-3 text-left font-medium">Latency</th>
                    <th className="p-3 text-left font-medium">Error</th>
                    <th className="p-3 text-left font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {evals.map((evalItem) => (
                    <EvalRow
                      key={evalItem.id}
                      evalItem={evalItem}
                      onDelete={() => handleDelete(evalItem)}
                      onRun={() => handleRun(evalItem)}
                      onUpdateComment={(comment) => handleUpdateComment(evalItem.id, comment)}
                      onUpdateErrorCategory={(cat) => handleUpdateErrorCategory(evalItem.id, cat)}
                      isDeleting={deletingId === evalItem.id}
                      isRunning={runningId === evalItem.id}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-lg rounded-lg bg-background p-6 shadow-lg">
            <h2 className="text-lg font-semibold">Add Evaluation Item</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Add a question to evaluate customer service responses.
            </p>
            <div className="mt-4 space-y-4">
              <div>
                <label className="text-sm font-medium">Question</label>
                <textarea
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  className="mt-1 h-24 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  placeholder="What is your return policy?"
                />
              </div>
              <div>
                <label className="text-sm font-medium">
                  Expected Source Documents (comma-separated, optional)
                </label>
                <input
                  type="text"
                  value={newGroundtruth}
                  onChange={(e) => setNewGroundtruth(e.target.value)}
                  className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm"
                  placeholder="returns-policy.pdf, faq.pdf"
                />
              </div>
              <div>
                <label className="text-sm font-medium">
                  Expected Answer (optional)
                </label>
                <textarea
                  value={newAnswerGroundtruth}
                  onChange={(e) => setNewAnswerGroundtruth(e.target.value)}
                  className="mt-1 h-20 w-full rounded-md border bg-background px-3 py-2 text-sm"
                  placeholder="The ideal response to compare against..."
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={createMutation.isPending}>
                {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add
              </Button>
            </div>
          </div>
        </div>
      )}

      {showGenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg bg-background p-6 shadow-lg">
            <h2 className="text-lg font-semibold">Generate Questions</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Use AI to generate evaluation questions from your documents.
            </p>
            <div className="mt-4 space-y-4">
              <div>
                <label className="text-sm font-medium">Collection</label>
                <select
                  value={selectedCollection}
                  onChange={(e) => setSelectedCollection(e.target.value)}
                  className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm"
                >
                  <option value="default">default</option>
                  {collections.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Number of Questions</label>
                <input
                  type="number"
                  value={numQuestions}
                  onChange={(e) => setNumQuestions(parseInt(e.target.value) || 5)}
                  min={1}
                  max={20}
                  className="mt-1 h-9 w-full rounded-md border bg-background px-3 text-sm"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowGenerateModal(false)}>
                Cancel
              </Button>
              <Button onClick={handleGenerate} disabled={generateMutation.isPending}>
                {generateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Generate
              </Button>
            </div>
          </div>
        </div>
      )}

      {showClaudeCodeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-2xl rounded-lg bg-background p-6 shadow-lg">
            <h2 className="text-lg font-semibold">Export to Claude Code</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Copy this prompt and paste it into your Claude Code terminal.
            </p>
            <div className="mt-4">
              <pre className="max-h-96 overflow-auto rounded-md border bg-muted p-4 text-xs">
                {claudeCodePrompt}
              </pre>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowClaudeCodeModal(false)}>
                Close
              </Button>
              <Button onClick={copyClaudeCodePrompt}>
                {copied ? (
                  <>
                    <Check className="mr-2 h-4 w-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Terminal className="mr-2 h-4 w-4" />
                    Copy to Clipboard
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
