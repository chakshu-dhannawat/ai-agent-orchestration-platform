import client from "./client";
import type { Workflow } from "@/types/workflow";

export interface TemplateInfo {
  id: string;
  name: string;
  description: string;
  agent_count: number;
  node_count: number;
  edge_count: number;
  agents: Array<Record<string, unknown>>;
  graph_definition: Record<string, unknown>;
}

export async function getTemplateCatalog(): Promise<TemplateInfo[]> {
  const response = await client.get<TemplateInfo[]>("/templates/catalog");
  return response.data;
}

export async function instantiateTemplate(
  templateId: string,
  name: string
): Promise<Workflow> {
  const response = await client.post<Workflow>(
    `/templates/catalog/${templateId}/instantiate`,
    { name }
  );
  return response.data;
}
