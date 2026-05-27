import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Save, X, Bot } from "lucide-react";
import Header from "@/components/layout/Header";
import { useAgentStore } from "@/store/agentStore";
import type { AgentCreate } from "@/types/agent";

const AVAILABLE_TOOLS = [
  "web_search",
  "code_interpreter",
  "file_reader",
  "api_caller",
  "database_query",
  "email_sender",
  "slack_notifier",
  "document_parser",
  "image_analyzer",
  "calculator",
  "json_processor",
  "csv_processor",
];

const AVAILABLE_CHANNELS = [
  "telegram",
  "slack",
  "discord",
  "webhook",
  "email",
  "api",
  "websocket",
];

const AVAILABLE_SKILLS = [
  "summarization",
  "translation",
  "classification",
  "extraction",
  "generation",
  "analysis",
  "qa",
  "coding",
];

const MODEL_OPTIONS = [
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4-turbo",
  "gpt-3.5-turbo",
  "claude-3-opus",
  "claude-3-sonnet",
  "claude-3-haiku",
  "claude-3.5-sonnet",
];

const defaultForm: AgentCreate & {
  guardrails_max_tokens: number;
  guardrails_blocked_topics: string;
  interaction_max_turns: number;
  interaction_handoff_target: string;
  schedule_cron: string;
} = {
  name: "",
  role: "",
  system_prompt: "",
  model: "gpt-4o-mini",
  tools: [],
  channels: [],
  memory_enabled: true,
  memory_window: 20,
  temperature: 0.7,
  max_tokens: 4096,
  skills: [],
  guardrails: {},
  interaction_rules: {},
  schedule: null,
  guardrails_max_tokens: 4096,
  guardrails_blocked_topics: "",
  interaction_max_turns: 10,
  interaction_handoff_target: "",
  schedule_cron: "",
};

export default function AgentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { fetchAgent, createAgent, updateAgent } = useAgentStore();
  const isNew = !id;

  const [form, setForm] = useState(defaultForm);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchAgent(id)
        .then((agent) => {
          const guardrails = agent.guardrails as Record<string, unknown>;
          const rules = agent.interaction_rules as Record<string, unknown>;
          setForm({
            name: agent.name,
            role: agent.role,
            system_prompt: agent.system_prompt,
            model: agent.model,
            tools: agent.tools,
            channels: agent.channels,
            memory_enabled: agent.memory_enabled,
            memory_window: agent.memory_window,
            temperature: agent.temperature,
            max_tokens: agent.max_tokens,
            skills: agent.skills,
            guardrails: agent.guardrails,
            interaction_rules: agent.interaction_rules,
            schedule: agent.schedule,
            guardrails_max_tokens:
              (guardrails.max_tokens as number) || 4096,
            guardrails_blocked_topics:
              ((guardrails.blocked_topics as string[]) || []).join(", "),
            interaction_max_turns:
              (rules.max_turns as number) || 10,
            interaction_handoff_target:
              (rules.handoff_target as string) || "",
            schedule_cron: agent.schedule?.cron || "",
          });
        })
        .catch(() => setLoadError("Failed to load agent"));
    }
  }, [id, fetchAgent]);

  function handleToolToggle(tool: string) {
    setForm((prev) => ({
      ...prev,
      tools: prev.tools?.includes(tool)
        ? prev.tools.filter((t) => t !== tool)
        : [...(prev.tools || []), tool],
    }));
  }

  function handleChannelToggle(channel: string) {
    setForm((prev) => ({
      ...prev,
      channels: prev.channels?.includes(channel)
        ? prev.channels.filter((c) => c !== channel)
        : [...(prev.channels || []), channel],
    }));
  }

  function handleSkillToggle(skill: string) {
    setForm((prev) => ({
      ...prev,
      skills: prev.skills?.includes(skill)
        ? prev.skills.filter((s) => s !== skill)
        : [...(prev.skills || []), skill],
    }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const guardrails: Record<string, unknown> = {
        max_tokens: form.guardrails_max_tokens,
      };
      if (form.guardrails_blocked_topics.trim()) {
        guardrails.blocked_topics = form.guardrails_blocked_topics
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      }

      const interaction_rules: Record<string, unknown> = {
        max_turns: form.interaction_max_turns,
      };
      if (form.interaction_handoff_target.trim()) {
        interaction_rules.handoff_target = form.interaction_handoff_target;
      }

      const schedule = form.schedule_cron.trim()
        ? { cron: form.schedule_cron.trim() }
        : null;

      const payload: AgentCreate = {
        name: form.name,
        role: form.role,
        system_prompt: form.system_prompt,
        model: form.model,
        tools: form.tools,
        channels: form.channels,
        memory_enabled: form.memory_enabled,
        memory_window: form.memory_window,
        temperature: form.temperature,
        max_tokens: form.max_tokens,
        skills: form.skills,
        guardrails,
        interaction_rules,
        schedule,
      };

      if (id) {
        await updateAgent(id, payload);
      } else {
        await createAgent(payload);
      }
      navigate("/agents");
    } catch {
      // Error is shown by the API interceptor
    } finally {
      setSaving(false);
    }
  }

  if (loadError) {
    return (
      <div className="text-center py-16 text-red-500">
        {loadError}
      </div>
    );
  }

  return (
    <div>
      <Header
        title={isNew ? "Create Agent" : `Edit Agent`}
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Agents", href: "/agents" },
          { label: isNew ? "New" : form.name || "Edit" },
        ]}
        actions={
          <div className="flex gap-2">
            <button className="btn-secondary" onClick={() => navigate("/agents")}>
              <X className="w-4 h-4" />
              Cancel
            </button>
            <button
              className="btn-primary"
              onClick={handleSave}
              disabled={saving || !form.name || !form.role}
            >
              <Save className="w-4 h-4" />
              {saving ? "Saving..." : "Save Agent"}
            </button>
          </div>
        }
      />

      <div className="max-w-4xl space-y-8">
        {/* Basic Info */}
        <section className="card p-6">
          <div className="flex items-center gap-2 mb-5">
            <Bot className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-slate-900">
              Basic Information
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Name</label>
              <input
                className="input"
                placeholder="e.g., Research Assistant"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Role</label>
              <input
                className="input"
                placeholder="e.g., researcher"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              />
            </div>
            <div className="md:col-span-2">
              <label className="label">System Prompt</label>
              <textarea
                className="textarea"
                rows={5}
                placeholder="Instructions for the agent..."
                value={form.system_prompt}
                onChange={(e) =>
                  setForm({ ...form, system_prompt: e.target.value })
                }
              />
            </div>
            <div>
              <label className="label">Model</label>
              <select
                className="select"
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
              >
                {MODEL_OPTIONS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">
                Temperature: {form.temperature?.toFixed(1)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                className="w-full mt-2"
                value={form.temperature}
                onChange={(e) =>
                  setForm({ ...form, temperature: parseFloat(e.target.value) })
                }
              />
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>Precise</span>
                <span>Creative</span>
              </div>
            </div>
          </div>
        </section>

        {/* Tools */}
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Tools</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {AVAILABLE_TOOLS.map((tool) => (
              <label
                key={tool}
                className={`flex items-center gap-2.5 p-3 rounded-lg border cursor-pointer transition-colors ${
                  form.tools?.includes(tool)
                    ? "border-blue-500 bg-blue-50"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={form.tools?.includes(tool) || false}
                  onChange={() => handleToolToggle(tool)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700">
                  {tool.replace(/_/g, " ")}
                </span>
              </label>
            ))}
          </div>
        </section>

        {/* Channels */}
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Channels</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {AVAILABLE_CHANNELS.map((channel) => (
              <label
                key={channel}
                className={`flex items-center gap-2.5 p-3 rounded-lg border cursor-pointer transition-colors ${
                  form.channels?.includes(channel)
                    ? "border-blue-500 bg-blue-50"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={form.channels?.includes(channel) || false}
                  onChange={() => handleChannelToggle(channel)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700">
                  {channel.charAt(0).toUpperCase() + channel.slice(1)}
                </span>
              </label>
            ))}
          </div>
        </section>

        {/* Skills */}
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Skills</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {AVAILABLE_SKILLS.map((skill) => (
              <label
                key={skill}
                className={`flex items-center gap-2.5 p-3 rounded-lg border cursor-pointer transition-colors ${
                  form.skills?.includes(skill)
                    ? "border-blue-500 bg-blue-50"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={form.skills?.includes(skill) || false}
                  onChange={() => handleSkillToggle(skill)}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-slate-700">
                  {skill.charAt(0).toUpperCase() + skill.slice(1)}
                </span>
              </label>
            ))}
          </div>
        </section>

        {/* Memory */}
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Memory</h2>
          <div className="flex items-center gap-4 mb-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.memory_enabled}
                onChange={(e) =>
                  setForm({ ...form, memory_enabled: e.target.checked })
                }
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-slate-700">
                Enable Memory
              </span>
            </label>
          </div>
          {form.memory_enabled && (
            <div>
              <label className="label">
                Memory Window: {form.memory_window} messages
              </label>
              <input
                type="range"
                min="1"
                max="100"
                className="w-full max-w-md"
                value={form.memory_window}
                onChange={(e) =>
                  setForm({
                    ...form,
                    memory_window: parseInt(e.target.value),
                  })
                }
              />
              <div className="flex justify-between text-xs text-slate-400 mt-1 max-w-md">
                <span>1</span>
                <span>50</span>
                <span>100</span>
              </div>
            </div>
          )}
        </section>

        {/* Guardrails */}
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Guardrails
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Max Output Tokens</label>
              <input
                type="number"
                className="input"
                min={1}
                max={128000}
                value={form.guardrails_max_tokens}
                onChange={(e) =>
                  setForm({
                    ...form,
                    guardrails_max_tokens: parseInt(e.target.value) || 4096,
                  })
                }
              />
            </div>
            <div>
              <label className="label">Blocked Topics (comma-separated)</label>
              <input
                className="input"
                placeholder="e.g., violence, personal data"
                value={form.guardrails_blocked_topics}
                onChange={(e) =>
                  setForm({
                    ...form,
                    guardrails_blocked_topics: e.target.value,
                  })
                }
              />
            </div>
          </div>
        </section>

        {/* Interaction Rules */}
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Interaction Rules
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Max Turns</label>
              <input
                type="number"
                className="input"
                min={1}
                max={100}
                value={form.interaction_max_turns}
                onChange={(e) =>
                  setForm({
                    ...form,
                    interaction_max_turns: parseInt(e.target.value) || 10,
                  })
                }
              />
            </div>
            <div>
              <label className="label">Handoff Target Agent</label>
              <input
                className="input"
                placeholder="Agent name to hand off to"
                value={form.interaction_handoff_target}
                onChange={(e) =>
                  setForm({
                    ...form,
                    interaction_handoff_target: e.target.value,
                  })
                }
              />
            </div>
          </div>
        </section>

        {/* Schedule */}
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Schedule
          </h2>
          <div>
            <label className="label">Cron Expression</label>
            <input
              className="input max-w-md"
              placeholder="e.g., 0 */6 * * * (every 6 hours)"
              value={form.schedule_cron}
              onChange={(e) =>
                setForm({ ...form, schedule_cron: e.target.value })
              }
            />
            <p className="text-xs text-slate-400 mt-1.5">
              Leave empty for no scheduled execution
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
