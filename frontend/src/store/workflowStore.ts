import { create } from "zustand";
import type { Workflow, WorkflowCreate, WorkflowUpdate } from "@/types/workflow";
import * as workflowsApi from "@/api/workflows";

interface WorkflowState {
  workflows: Workflow[];
  loading: boolean;
  error: string | null;
  fetchWorkflows: () => Promise<void>;
  fetchWorkflow: (id: string) => Promise<Workflow>;
  createWorkflow: (data: WorkflowCreate) => Promise<Workflow>;
  updateWorkflow: (id: string, data: WorkflowUpdate) => Promise<Workflow>;
  deleteWorkflow: (id: string) => Promise<void>;
  validateWorkflow: (
    id: string
  ) => Promise<{ valid: boolean; errors: string[] }>;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  workflows: [],
  loading: false,
  error: null,

  fetchWorkflows: async () => {
    set({ loading: true, error: null });
    try {
      const workflows = await workflowsApi.getWorkflows();
      set({ workflows, loading: false });
    } catch (err) {
      set({
        error:
          err instanceof Error ? err.message : "Failed to fetch workflows",
        loading: false,
      });
    }
  },

  fetchWorkflow: async (id: string) => {
    const workflow = await workflowsApi.getWorkflow(id);
    const workflows = get().workflows;
    const idx = workflows.findIndex((w) => w.id === id);
    if (idx >= 0) {
      const updated = [...workflows];
      updated[idx] = workflow;
      set({ workflows: updated });
    } else {
      set({ workflows: [...workflows, workflow] });
    }
    return workflow;
  },

  createWorkflow: async (data: WorkflowCreate) => {
    const workflow = await workflowsApi.createWorkflow(data);
    set({ workflows: [...get().workflows, workflow] });
    return workflow;
  },

  updateWorkflow: async (id: string, data: WorkflowUpdate) => {
    const workflow = await workflowsApi.updateWorkflow(id, data);
    set({
      workflows: get().workflows.map((w) => (w.id === id ? workflow : w)),
    });
    return workflow;
  },

  deleteWorkflow: async (id: string) => {
    await workflowsApi.deleteWorkflow(id);
    set({ workflows: get().workflows.filter((w) => w.id !== id) });
  },

  validateWorkflow: async (id: string) => {
    return workflowsApi.validateWorkflow(id);
  },
}));
