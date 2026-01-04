"use client";

import { useState } from "react";
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
  useCollections,
} from "@/hooks";
import type { EvalItem } from "@/types/api";

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

function EvalRow({
  evalItem,
  onDelete,
  onRun,
  onUpdateComment,
  isDeleting,
  isRunning,
  collectionName,
}: {
  evalItem: EvalItem;
  onDelete: () => void;
  onRun: () => void;
  onUpdateComment: (comment: string) => void;
  isDeleting: boolean;
  isRunning: boolean;
  collectionName: string;
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
            <span className="max-w-[300px] truncate font-medium">{evalItem.question}</span>
          </button>
        </td>
        <td className="p-3">
          {evalItem.response ? (
            <span className="block max-w-[250px] truncate text-sm text-muted-foreground">
              {evalItem.response}
            </span>
          ) : (
            <span className="text-sm text-muted-foreground">—</span>
          )}
        </td>
        <td className="p-3">
          <div className="flex flex-wrap gap-1">
            {evalItem.sources?.slice(0, 2).map((source, i) => (
              <Badge key={i} variant="secondary" className="max-w-[120px] truncate text-xs">
                {source.split(" (")[0]}
              </Badge>
            ))}
            {evalItem.sources && evalItem.sources.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{evalItem.sources.length - 2}
              </Badge>
            )}
            {!evalItem.sources?.length && <span className="text-sm text-muted-foreground">—</span>}
          </div>
        </td>
        <td className="p-3">
          <div className="flex flex-wrap gap-1">
            {evalItem.sources_groundtruth?.slice(0, 2).map((source, i) => (
              <Badge key={i} variant="outline" className="max-w-[120px] truncate text-xs border-green-500 text-green-600">
                {source}
              </Badge>
            ))}
            {evalItem.sources_groundtruth && evalItem.sources_groundtruth.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{evalItem.sources_groundtruth.length - 2}
              </Badge>
            )}
            {!evalItem.sources_groundtruth?.length && (
              <span className="text-sm text-muted-foreground">—</span>
            )}
          </div>
        </td>
        <td className="p-3">
          {editingComment ? (
            <div className="flex items-center gap-1">
              <input
                type="text"
                value={commentValue}
                onChange={(e) => setCommentValue(e.target.value)}
                className="h-7 w-32 rounded border bg-background px-2 text-sm"
                autoFocus
              />
              <Button variant="ghost" size="sm" onClick={handleSaveComment}>
                <Check className="h-3 w-3 text-green-600" />
              </Button>
              <Button variant="ghost" size="sm" onClick={handleCancelComment}>
                <X className="h-3 w-3 text-red-600" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-1">
              <span className="max-w-[100px] truncate text-sm text-muted-foreground">
                {evalItem.comment || "—"}
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
        </td>
        <td className="p-3">
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatLatency(evalItem.latency_ms)}
          </div>
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
          <td colSpan={7} className="p-4">
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
              {evalItem.conversation_history && (
                <div>
                  <h4 className="text-sm font-medium">Conversation History</h4>
                  <pre className="mt-1 max-h-48 overflow-auto rounded bg-muted p-2 text-xs">
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
          </td>
        </tr>
      )}
    </>
  );
}

export default function EvalsPage() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [newQuestion, setNewQuestion] = useState("");
  const [newGroundtruth, setNewGroundtruth] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const [selectedCollection, setSelectedCollection] = useState("default");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);

  const { data, isLoading } = useEvals();
  const { data: collectionsData } = useCollections();
  const createMutation = useCreateEval();
  const updateMutation = useUpdateEval();
  const deleteMutation = useDeleteEval();
  const generateMutation = useGenerateQuestions();
  const runMutation = useRunEval();

  const evals = data?.items ?? [];
  const collections = collectionsData?.items ?? [];

  const handleCreate = async () => {
    if (!newQuestion.trim()) return;

    await createMutation.mutateAsync({
      question: newQuestion,
      sources_groundtruth: newGroundtruth ? newGroundtruth.split(",").map((s) => s.trim()) : null,
    });
    setNewQuestion("");
    setNewGroundtruth("");
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

  const handleUpdateComment = async (evalId: string, comment: string) => {
    await updateMutation.mutateAsync({
      evalId,
      data: { comment },
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
      });
    }

    setShowGenerateModal(false);
  };

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
          <Button variant="outline" onClick={() => setShowGenerateModal(true)}>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate Questions
          </Button>
          <Button onClick={() => setShowAddModal(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Eval
          </Button>
        </div>
      </div>

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
                    <th className="p-3 text-left font-medium">Response</th>
                    <th className="p-3 text-left font-medium">Sources</th>
                    <th className="p-3 text-left font-medium">Groundtruth</th>
                    <th className="p-3 text-left font-medium">Comment</th>
                    <th className="p-3 text-left font-medium">Latency</th>
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
                      isDeleting={deletingId === evalItem.id}
                      isRunning={runningId === evalItem.id}
                      collectionName={selectedCollection}
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
    </div>
  );
}
