import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BookTemplate,
  Users,
  Sparkles,
  GitBranch,
} from "lucide-react";
import Header from "@/components/layout/Header";
import * as templatesApi from "@/api/templates";
import type { TemplateInfo } from "@/api/templates";

export default function TemplateGallery() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [instantiating, setInstantiating] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  async function loadTemplates() {
    setLoading(true);
    try {
      const data = await templatesApi.getTemplateCatalog();
      setTemplates(data);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  }

  async function handleUseTemplate(templateId: string) {
    const name = window.prompt("Enter a name for the new workflow:");
    if (!name) return;

    setInstantiating(templateId);
    try {
      const workflow = await templatesApi.instantiateTemplate(templateId, name);
      navigate(`/workflows/${workflow.id}`);
    } catch {
      // handled by interceptor
    } finally {
      setInstantiating(null);
    }
  }

  function getAgentNames(template: TemplateInfo): string[] {
    return template.agents
      .map((a) => (a.name as string) || (a.role as string) || "Agent")
      .slice(0, 5);
  }

  return (
    <div>
      <Header
        title="Template Gallery"
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Templates" },
        ]}
      />

      {loading && (
        <div className="text-center py-12 text-slate-400">
          Loading templates...
        </div>
      )}

      {!loading && templates.length === 0 && (
        <div className="text-center py-16">
          <BookTemplate className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            No templates available
          </h3>
          <p className="text-sm text-slate-500">
            Templates are pre-built workflow configurations you can use as
            starting points
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map((template) => {
          const agentNames = getAgentNames(template);
          return (
            <div key={template.id} className="card overflow-hidden">
              <div className="bg-gradient-to-br from-blue-600 to-violet-600 px-6 py-5">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5 text-white/80" />
                  <h3 className="text-lg font-semibold text-white">
                    {template.name}
                  </h3>
                </div>
                {template.description && (
                  <p className="text-sm text-white/70 line-clamp-2">
                    {template.description}
                  </p>
                )}
              </div>

              <div className="p-5">
                {agentNames.length > 0 && (
                  <div className="mb-4">
                    <h4 className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                      <Users className="w-3.5 h-3.5" />
                      Agents ({template.agent_count})
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {agentNames.map((name, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 rounded text-xs text-slate-600"
                        >
                          {name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center gap-3 text-xs text-slate-400 mb-4">
                  <span className="flex items-center gap-1">
                    <GitBranch className="w-3.5 h-3.5" />
                    {template.node_count} nodes, {template.edge_count} edges
                  </span>
                </div>

                <button
                  className="btn-primary w-full justify-center"
                  onClick={() => handleUseTemplate(template.id)}
                  disabled={instantiating === template.id}
                >
                  {instantiating === template.id
                    ? "Creating..."
                    : "Use Template"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
