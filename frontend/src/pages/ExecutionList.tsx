import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  Activity,
  Coins,
  Zap,
} from "lucide-react";
import Header from "@/components/layout/Header";
import { useExecutionStore } from "@/store/executionStore";
import { useWorkflowStore } from "@/store/workflowStore";

export default function ExecutionList() {
  const navigate = useNavigate();
  const { executions, loading, fetchExecutions } = useExecutionStore();
  const { workflows, fetchWorkflows } = useWorkflowStore();

  useEffect(() => {
    fetchExecutions();
    fetchWorkflows();
  }, [fetchExecutions, fetchWorkflows]);

  function getWorkflowName(workflowId: string): string {
    return workflows.find((w) => w.id === workflowId)?.name || "Unknown";
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "running":
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      case "cancelled":
        return <XCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  }

  function getStatusBadge(status: string): string {
    const map: Record<string, string> = {
      completed: "badge-green",
      failed: "badge-red",
      running: "badge-blue",
      pending: "badge-gray",
      cancelled: "badge-yellow",
    };
    return map[status] || "badge-gray";
  }

  function formatDuration(start: string | null, end: string | null): string {
    if (!start) return "-";
    const s = new Date(start).getTime();
    const e = end ? new Date(end).getTime() : Date.now();
    const seconds = Math.floor((e - s) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  }

  function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function formatTokens(n: number): string {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
    return n.toString();
  }

  const sorted = [...executions].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div>
      <Header
        title="Executions"
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Executions" },
        ]}
      />

      {loading && (
        <div className="text-center py-12 text-slate-400">
          Loading executions...
        </div>
      )}

      {!loading && sorted.length === 0 && (
        <div className="text-center py-16">
          <Play className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            No executions yet
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            Run a workflow to see executions here
          </p>
          <Link to="/workflows" className="btn-primary">
            Go to Workflows
          </Link>
        </div>
      )}

      {sorted.length > 0 && (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Workflow
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Started
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <div className="flex items-center gap-1">
                    <Zap className="w-3.5 h-3.5" /> Tokens
                  </div>
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <div className="flex items-center gap-1">
                    <Coins className="w-3.5 h-3.5" /> Cost
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sorted.map((exec) => (
                <tr
                  key={exec.id}
                  className="hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/executions/${exec.id}`)}
                >
                  <td className="px-6 py-3.5">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(exec.status)}
                      <span className={getStatusBadge(exec.status)}>
                        {exec.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-3.5">
                    <div>
                      <p className="text-sm font-medium text-slate-900">
                        {getWorkflowName(exec.workflow_id)}
                      </p>
                      <p className="text-xs text-slate-400 font-mono">
                        {exec.id.slice(0, 8)}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-600">
                    {exec.started_at
                      ? formatDateTime(exec.started_at)
                      : "-"}
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-600 font-mono">
                    {formatDuration(exec.started_at, exec.completed_at)}
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-600 font-mono">
                    {formatTokens(exec.total_tokens)}
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-600 font-mono">
                    ${exec.estimated_cost_usd.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
