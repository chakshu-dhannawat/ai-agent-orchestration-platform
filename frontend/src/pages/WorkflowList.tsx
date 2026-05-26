import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  GitBranch,
  Plus,
  Trash2,
  Edit,
  Search,
  Users,
  Clock,
} from "lucide-react";
import Header from "@/components/layout/Header";
import { useWorkflowStore } from "@/store/workflowStore";

export default function WorkflowList() {
  const navigate = useNavigate();
  const { workflows, loading, fetchWorkflows, deleteWorkflow } =
    useWorkflowStore();
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const filtered = workflows.filter(
    (w) =>
      !w.is_template &&
      (w.name.toLowerCase().includes(search.toLowerCase()) ||
        w.description.toLowerCase().includes(search.toLowerCase()))
  );

  async function handleDelete(id: string) {
    if (!window.confirm("Are you sure you want to delete this workflow?"))
      return;
    setDeleting(id);
    try {
      await deleteWorkflow(id);
    } finally {
      setDeleting(null);
    }
  }

  function getAgentCount(workflow: (typeof workflows)[0]): number {
    const graph = workflow.graph_definition;
    if (!graph || !graph.nodes) return 0;
    return (graph.nodes as Array<{ type?: string }>).filter(
      (n) => n.type === "agent"
    ).length;
  }

  function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  return (
    <div>
      <Header
        title="Workflows"
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Workflows" },
        ]}
        actions={
          <Link to="/workflows/new" className="btn-primary">
            <Plus className="w-4 h-4" />
            Create Workflow
          </Link>
        }
      />

      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Search workflows..."
          className="input pl-10"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {loading && (
        <div className="text-center py-12 text-slate-400">
          Loading workflows...
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-16">
          <GitBranch className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            {search ? "No workflows match your search" : "No workflows yet"}
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            {search
              ? "Try a different search term"
              : "Create your first workflow to orchestrate agents"}
          </p>
          {!search && (
            <Link to="/workflows/new" className="btn-primary">
              <Plus className="w-4 h-4" />
              Create Workflow
            </Link>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((workflow) => (
          <div
            key={workflow.id}
            className="card p-5 cursor-pointer group"
            onClick={() => navigate(`/workflows/${workflow.id}`)}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 bg-violet-100 rounded-lg">
                  <GitBranch className="w-5 h-5 text-violet-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    {workflow.name}
                  </h3>
                  {workflow.description && (
                    <p className="text-xs text-slate-500 line-clamp-1">
                      {workflow.description}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/workflows/${workflow.id}`);
                  }}
                  className="p-1.5 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(workflow.id);
                  }}
                  disabled={deleting === workflow.id}
                  className="p-1.5 rounded-md hover:bg-red-50 text-slate-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex items-center gap-4 mt-4 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Users className="w-3.5 h-3.5" />
                {getAgentCount(workflow)} agents
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {formatDate(workflow.updated_at)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
