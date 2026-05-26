import client from "./client";
import type { Agent, AgentCreate, AgentUpdate } from "@/types/agent";

export async function getAgents(): Promise<Agent[]> {
  const response = await client.get<Agent[]>("/agents");
  return response.data;
}

export async function getAgent(id: string): Promise<Agent> {
  const response = await client.get<Agent>(`/agents/${id}`);
  return response.data;
}

export async function createAgent(data: AgentCreate): Promise<Agent> {
  const response = await client.post<Agent>("/agents", data);
  return response.data;
}

export async function updateAgent(
  id: string,
  data: AgentUpdate
): Promise<Agent> {
  const response = await client.put<Agent>(`/agents/${id}`, data);
  return response.data;
}

export async function deleteAgent(id: string): Promise<void> {
  await client.delete(`/agents/${id}`);
}
