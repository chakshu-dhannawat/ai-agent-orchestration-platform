import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Bot,
  Plus,
  Search,
  Wrench,
  Trash2,
  Edit,
  Brain,
  Cpu,
} from "lucide-react";
import Header from "@/components/layout/Header";
import { useAgentStore } from "@/store/agentStore";

export default function AgentList() {
  const navigate = useNavigate();
  const { agents, loading, fetchAgents, deleteAgent } = useAgentStore();
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const filtered = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.role.toLowerCase().includes(search.toLowerCase()) ||
      a.model.toLowerCase().includes(search.toLowerCase())
  );

  async function handleDelete(id: string) {
    if (!window.confirm("Are you sure you want to delete this agent?")) return;
    setDeleting(id);
    try {
      await deleteAgent(id);
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div>
      <Header
        title="Agents"
        breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Agents" }]}
        actions={
          <Link to="/agents/new" className="btn-primary">
            <Plus className="w-4 h-4" />
            Create Agent
          </Link>
        }
      />

      {/* Search Bar */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Search agents by name, role, or model..."
          className="input pl-10"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-12 text-slate-400">
          Loading agents...
        </div>
      )}

      {/* Empty State */}
      {!loading && filtered.length === 0 && (
        <div className="text-center py-16">
          <Bot className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            {search ? "No agents match your search" : "No agents yet"}
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            {search
              ? "Try a different search term"
              : "Create your first AI agent to get started"}
          </p>
          {!search && (
            <Link to="/agents/new" className="btn-primary">
              <Plus className="w-4 h-4" />
              Create Agent
            </Link>
          )}
        </div>
      )}

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((agent) => (
          <div
            key={agent.id}
            className="card p-5 cursor-pointer group"
            onClick={() => navigate(`/agents/${agent.id}`)}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg">
                  <Bot className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    {agent.name}
                  </h3>
                  <p className="text-xs text-slate-500">{agent.role}</p>
                </div>
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/agents/${agent.id}`);
                  }}
                  className="p-1.5 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(agent.id);
                  }}
                  disabled={deleting === agent.id}
                  className="p-1.5 rounded-md hover:bg-red-50 text-slate-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mt-3">
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 rounded text-xs text-slate-600">
                <Cpu className="w-3 h-3" />
                {agent.model}
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 rounded text-xs text-slate-600">
                <Wrench className="w-3 h-3" />
                {agent.tools.length} tools
              </span>
              {agent.memory_enabled && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-violet-50 rounded text-xs text-violet-600">
                  <Brain className="w-3 h-3" />
                  Memory
                </span>
              )}
            </div>

            {agent.system_prompt && (
              <p className="mt-3 text-xs text-slate-400 line-clamp-2">
                {agent.system_prompt}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
