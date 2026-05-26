import client from "./client";
import type { Workflow } from "@/types/workflow";

export async function getTemplates(): Promise<Workflow[]> {
  const response = await client.get<Workflow[]>("/workflows/templates");
  return response.data;
}

export async function instantiateTemplate(
  templateId: string,
  name: string
): Promise<Workflow> {
  const response = await client.post<Workflow>(
    `/workflows/templates/${templateId}/instantiate`,
    { name }
  );
  return response.data;
}
