import { useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Bot,
  GitBranch,
  Play,
  Plus,
  ArrowRight,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  BookTemplate,
} from "lucide-react";
import Header from "@/components/layout/Header";
import { useAgentStore } from "@/store/agentStore";
import { useWorkflowStore } from "@/store/workflowStore";
import { useExecutionStore } from "@/store/executionStore";

export default function Dashboard() {
  const { agents, fetchAgents } = useAgentStore();
  const { workflows, fetchWorkflows } = useWorkflowStore();
  const { executions, fetchExecutions } = useExecutionStore();

  useEffect(() => {
    fetchAgents();
    fetchWorkflows();
    fetchExecutions();
  }, [fetchAgents, fetchWorkflows, fetchExecutions]);

  const recentExecutions = [...executions]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    .slice(0, 5);

  const runningCount = executions.filter((e) => e.status === "running").length;
  const completedCount = executions.filter(
    (e) => e.status === "completed"
  ).length;
  const failedCount = executions.filter((e) => e.status === "failed").length;

  function getStatusIcon(status: string) {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "running":
        return <Activity className="w-4 h-4 text-blue-500 animate-pulse" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  }

  function getStatusBadge(status: string) {
    const classes: Record<string, string> = {
      completed: "badge-green",
      failed: "badge-red",
      running: "badge-blue",
      pending: "badge-gray",
      cancelled: "badge-yellow",
    };
    return classes[status] || "badge-gray";
  }

  function formatRelativeTime(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  return (
    <div>
      <Header
        title="Dashboard"
        actions={
          <div className="flex gap-2">
            <Link to="/templates" className="btn-secondary inline-flex items-center gap-1.5">
              <BookTemplate className="w-4 h-4" />
              Templates
            </Link>
            <Link to="/agents/new" className="btn-primary">
              <Plus className="w-4 h-4" />
              New Agent
            </Link>
            <Link to="/workflows/new" className="btn-secondary">
              <Plus className="w-4 h-4" />
              New Workflow
            </Link>
          </div>
        }
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-slate-500">
              Total Agents
            </span>
            <Bot className="w-5 h-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-slate-900">{agents.length}</p>
          <Link
            to="/agents"
            className="text-sm text-blue-600 hover:text-blue-700 mt-2 inline-flex items-center gap-1"
          >
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-slate-500">
              Workflows
            </span>
            <GitBranch className="w-5 h-5 text-violet-500" />
          </div>
          <p className="text-3xl font-bold text-slate-900">
            {workflows.length}
          </p>
          <Link
            to="/workflows"
            className="text-sm text-blue-600 hover:text-blue-700 mt-2 inline-flex items-center gap-1"
          >
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-slate-500">
              Running Now
            </span>
            <Activity className="w-5 h-5 text-emerald-500" />
          </div>
          <p className="text-3xl font-bold text-slate-900">{runningCount}</p>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-500" />
              {completedCount} completed
            </span>
            <span className="flex items-center gap-1">
              <XCircle className="w-3 h-3 text-red-500" />
              {failedCount} failed
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-slate-500">
              Total Executions
            </span>
            <Play className="w-5 h-5 text-amber-500" />
          </div>
          <p className="text-3xl font-bold text-slate-900">
            {executions.length}
          </p>
          <Link
            to="/executions"
            className="text-sm text-blue-600 hover:text-blue-700 mt-2 inline-flex items-center gap-1"
          >
            View all <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="card">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            Recent Executions
          </h2>
          <Link
            to="/executions"
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            View all
          </Link>
        </div>
        <div className="divide-y divide-slate-100">
          {recentExecutions.length === 0 && (
            <div className="px-6 py-12 text-center text-slate-400">
              <Play className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p>No executions yet. Run a workflow to get started.</p>
            </div>
          )}
          {recentExecutions.map((exec) => {
            const workflow = workflows.find((w) => w.id === exec.workflow_id);
            return (
              <Link
                key={exec.id}
                to={`/executions/${exec.id}`}
                className="flex items-center px-6 py-3.5 hover:bg-slate-50 transition-colors"
              >
                <div className="mr-3">{getStatusIcon(exec.status)}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {workflow?.name || "Unknown Workflow"}
                  </p>
                  <p className="text-xs text-slate-500">
                    {exec.id.slice(0, 8)}...
                  </p>
                </div>
                <span className={getStatusBadge(exec.status)}>
                  {exec.status}
                </span>
                <span className="ml-4 text-xs text-slate-400 shrink-0">
                  {formatRelativeTime(exec.created_at)}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
