import client from "./client";
import type { Workflow, WorkflowCreate, WorkflowUpdate } from "@/types/workflow";

export async function getWorkflows(): Promise<Workflow[]> {
  const response = await client.get<Workflow[]>("/workflows");
  return response.data;
}

export async function getWorkflow(id: string): Promise<Workflow> {
  const response = await client.get<Workflow>(`/workflows/${id}`);
  return response.data;
}

export async function createWorkflow(data: WorkflowCreate): Promise<Workflow> {
  const response = await client.post<Workflow>("/workflows", data);
  return response.data;
}

export async function updateWorkflow(
  id: string,
  data: WorkflowUpdate
): Promise<Workflow> {
  const response = await client.put<Workflow>(`/workflows/${id}`, data);
  return response.data;
}

export async function deleteWorkflow(id: string): Promise<void> {
  await client.delete(`/workflows/${id}`);
}

export async function validateWorkflow(
  id: string
): Promise<{ valid: boolean; errors: string[] }> {
  const response = await client.post<{ valid: boolean; errors: string[] }>(
    `/workflows/${id}/validate`
  );
  return response.data;
}
