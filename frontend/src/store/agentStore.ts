import { create } from "zustand";
import type { Agent, AgentCreate, AgentUpdate } from "@/types/agent";
import * as agentsApi from "@/api/agents";

interface AgentState {
  agents: Agent[];
  loading: boolean;
  error: string | null;
  fetchAgents: () => Promise<void>;
  fetchAgent: (id: string) => Promise<Agent>;
  createAgent: (data: AgentCreate) => Promise<Agent>;
  updateAgent: (id: string, data: AgentUpdate) => Promise<Agent>;
  deleteAgent: (id: string) => Promise<void>;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  loading: false,
  error: null,

  fetchAgents: async () => {
    set({ loading: true, error: null });
    try {
      const agents = await agentsApi.getAgents();
      set({ agents, loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : "Failed to fetch agents",
        loading: false,
      });
    }
  },

  fetchAgent: async (id: string) => {
    const agent = await agentsApi.getAgent(id);
    const agents = get().agents;
    const idx = agents.findIndex((a) => a.id === id);
    if (idx >= 0) {
      const updated = [...agents];
      updated[idx] = agent;
      set({ agents: updated });
    } else {
      set({ agents: [...agents, agent] });
    }
    return agent;
  },

  createAgent: async (data: AgentCreate) => {
    const agent = await agentsApi.createAgent(data);
    set({ agents: [...get().agents, agent] });
    return agent;
  },

  updateAgent: async (id: string, data: AgentUpdate) => {
    const agent = await agentsApi.updateAgent(id, data);
    set({
      agents: get().agents.map((a) => (a.id === id ? agent : a)),
    });
    return agent;
  },

  deleteAgent: async (id: string) => {
    await agentsApi.deleteAgent(id);
    set({ agents: get().agents.filter((a) => a.id !== id) });
  },
}));
