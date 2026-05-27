import { create } from "zustand";
import type { Execution, ExecutionCreate, ExecutionLog } from "@/types/execution";
import type { AgentMessage } from "@/types/message";
import * as executionsApi from "@/api/executions";

interface ExecutionState {
  executions: Execution[];
  activeExecution: Execution | null;
  logs: ExecutionLog[];
  messages: AgentMessage[];
  loading: boolean;
  error: string | null;
  fetchExecutions: () => Promise<void>;
  fetchExecution: (id: string) => Promise<Execution>;
  startExecution: (data: ExecutionCreate) => Promise<Execution>;
  cancelExecution: (id: string) => Promise<void>;
  fetchExecutionLogs: (id: string) => Promise<void>;
  fetchExecutionMessages: (id: string) => Promise<void>;
  setActiveExecution: (execution: Execution | null) => void;
  addLog: (log: ExecutionLog) => void;
  addMessage: (message: AgentMessage) => void;
  updateExecutionStatus: (
    id: string,
    status: Execution["status"],
    currentNode?: string | null
  ) => void;
  updateExecutionTokens: (
    id: string,
    tokens: Partial<Pick<Execution, "total_tokens" | "prompt_tokens" | "completion_tokens" | "estimated_cost_usd">>
  ) => void;
}

export const useExecutionStore = create<ExecutionState>((set, get) => ({
  executions: [],
  activeExecution: null,
  logs: [],
  messages: [],
  loading: false,
  error: null,

  fetchExecutions: async () => {
    set({ loading: true, error: null });
    try {
      const executions = await executionsApi.getExecutions();
      set({ executions, loading: false });
    } catch (err) {
      set({
        error:
          err instanceof Error ? err.message : "Failed to fetch executions",
        loading: false,
      });
    }
  },

  fetchExecution: async (id: string) => {
    const execution = await executionsApi.getExecution(id);
    set({ activeExecution: execution });
    const executions = get().executions;
    const idx = executions.findIndex((e) => e.id === id);
    if (idx >= 0) {
      const updated = [...executions];
      updated[idx] = execution;
      set({ executions: updated });
    }
    return execution;
  },

  startExecution: async (data: ExecutionCreate) => {
    const execution = await executionsApi.startExecution(data);
    set({
      executions: [execution, ...get().executions],
      activeExecution: execution,
      logs: [],
      messages: [],
    });
    return execution;
  },

  cancelExecution: async (id: string) => {
    const execution = await executionsApi.cancelExecution(id);
    set({
      activeExecution: execution,
      executions: get().executions.map((e) => (e.id === id ? execution : e)),
    });
  },

  fetchExecutionLogs: async (id: string) => {
    const logs = await executionsApi.getExecutionLogs(id);
    set({ logs });
  },

  fetchExecutionMessages: async (id: string) => {
    const messages = await executionsApi.getExecutionMessages(id);
    set({ messages });
  },

  setActiveExecution: (execution: Execution | null) => {
    set({ activeExecution: execution });
  },

  addLog: (log: ExecutionLog) => {
    set({ logs: [...get().logs, log] });
  },

  addMessage: (message: AgentMessage) => {
    set({ messages: [...get().messages, message] });
  },

  updateExecutionStatus: (
    id: string,
    status: Execution["status"],
    currentNode?: string | null
  ) => {
    const update = (e: Execution) =>
      e.id === id ? { ...e, status, current_node: currentNode ?? e.current_node } : e;
    set({
      executions: get().executions.map(update),
      activeExecution:
        get().activeExecution?.id === id
          ? update(get().activeExecution!)
          : get().activeExecution,
    });
  },

  updateExecutionTokens: (
    id: string,
    tokens: Partial<Pick<Execution, "total_tokens" | "prompt_tokens" | "completion_tokens" | "estimated_cost_usd">>
  ) => {
    const update = (e: Execution) =>
      e.id === id ? { ...e, ...tokens } : e;
    set({
      executions: get().executions.map(update),
      activeExecution:
        get().activeExecution?.id === id
          ? update(get().activeExecution!)
          : get().activeExecution,
    });
  },
}));
