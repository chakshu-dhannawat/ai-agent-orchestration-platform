import { useEffect, useState } from "react";
import {
  Radio,
  Plus,
  Trash2,
  CheckCircle2,
  XCircle,
  X,
} from "lucide-react";
import Header from "@/components/layout/Header";
import * as channelsApi from "@/api/channels";
import type { Channel, ChannelCreate } from "@/types/channel";

const CHANNEL_TYPES = [
  "slack",
  "discord",
  "webhook",
  "email",
  "api",
  "websocket",
];

export default function ChannelList() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<ChannelCreate>({
    type: "webhook",
    name: "",
    config: {},
    is_active: true,
  });

  useEffect(() => {
    loadChannels();
  }, []);

  async function loadChannels() {
    setLoading(true);
    try {
      const data = await channelsApi.getChannels();
      setChannels(data);
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const channel = await channelsApi.createChannel(form);
      setChannels((prev) => [...prev, channel]);
      setShowForm(false);
      setForm({ type: "webhook", name: "", config: {}, is_active: true });
    } catch {
      // handled by interceptor
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this channel?")) return;
    setDeleting(id);
    try {
      await channelsApi.deleteChannel(id);
      setChannels((prev) => prev.filter((c) => c.id !== id));
    } catch {
      // handled by interceptor
    } finally {
      setDeleting(null);
    }
  }

  function getTypeColor(type: string): string {
    const colors: Record<string, string> = {
      slack: "bg-purple-100 text-purple-700",
      discord: "bg-indigo-100 text-indigo-700",
      webhook: "bg-blue-100 text-blue-700",
      email: "bg-amber-100 text-amber-700",
      api: "bg-emerald-100 text-emerald-700",
      websocket: "bg-cyan-100 text-cyan-700",
    };
    return colors[type] || "bg-slate-100 text-slate-700";
  }

  return (
    <div>
      <Header
        title="Channels"
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Channels" },
        ]}
        actions={
          <button
            className="btn-primary"
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? (
              <>
                <X className="w-4 h-4" />
                Cancel
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                Add Channel
              </>
            )}
          </button>
        }
      />

      {/* Add Channel Form */}
      {showForm && (
        <div className="card p-6 mb-6">
          <h3 className="text-sm font-semibold text-slate-900 mb-4">
            New Channel
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Type</label>
              <select
                className="select"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                {CHANNEL_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Name</label>
              <input
                className="input"
                placeholder="e.g., Production Webhook"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="flex items-end">
              <button
                className="btn-primary w-full justify-center"
                onClick={handleCreate}
                disabled={saving || !form.name.trim()}
              >
                {saving ? "Creating..." : "Create Channel"}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="text-center py-12 text-slate-400">
          Loading channels...
        </div>
      )}

      {!loading && channels.length === 0 && !showForm && (
        <div className="text-center py-16">
          <Radio className="w-12 h-12 mx-auto mb-3 text-slate-300" />
          <h3 className="text-lg font-medium text-slate-900 mb-1">
            No channels configured
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            Channels connect your agents to external services
          </p>
          <button className="btn-primary" onClick={() => setShowForm(true)}>
            <Plus className="w-4 h-4" />
            Add Channel
          </button>
        </div>
      )}

      {channels.length > 0 && (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Connected Agent
                </th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="text-right px-6 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {channels.map((channel) => (
                <tr key={channel.id} className="hover:bg-slate-50">
                  <td className="px-6 py-3.5">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getTypeColor(
                        channel.type
                      )}`}
                    >
                      {channel.type}
                    </span>
                  </td>
                  <td className="px-6 py-3.5">
                    <p className="text-sm font-medium text-slate-900">
                      {channel.name}
                    </p>
                  </td>
                  <td className="px-6 py-3.5">
                    <div className="flex items-center gap-1.5">
                      {channel.is_active ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                          <span className="text-sm text-emerald-700">
                            Active
                          </span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-slate-400" />
                          <span className="text-sm text-slate-500">
                            Inactive
                          </span>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-600">
                    {channel.agent_id
                      ? channel.agent_id.slice(0, 8) + "..."
                      : "-"}
                  </td>
                  <td className="px-6 py-3.5 text-sm text-slate-500">
                    {new Date(channel.created_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })}
                  </td>
                  <td className="px-6 py-3.5 text-right">
                    <button
                      onClick={() => handleDelete(channel.id)}
                      disabled={deleting === channel.id}
                      className="p-1.5 rounded-md hover:bg-red-50 text-slate-400 hover:text-red-600 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
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
