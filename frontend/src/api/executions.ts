import client from "./client";
import type {
  Execution,
  ExecutionCreate,
  ExecutionLog,
} from "@/types/execution";
import type { AgentMessage } from "@/types/message";

export async function startExecution(
  data: ExecutionCreate
): Promise<Execution> {
  const response = await client.post<Execution>("/executions", data);
  return response.data;
}

export async function getExecutions(): Promise<Execution[]> {
  const response = await client.get<Execution[]>("/executions");
  return response.data;
}

export async function getExecution(id: string): Promise<Execution> {
  const response = await client.get<Execution>(`/executions/${id}`);
  return response.data;
}

export async function cancelExecution(id: string): Promise<Execution> {
  const response = await client.post<Execution>(`/executions/${id}/cancel`);
  return response.data;
}

export async function getExecutionMessages(
  id: string
): Promise<AgentMessage[]> {
  const response = await client.get<AgentMessage[]>(
    `/executions/${id}/messages`
  );
  return response.data;
}

export async function getExecutionLogs(id: string): Promise<ExecutionLog[]> {
  const response = await client.get<ExecutionLog[]>(`/executions/${id}/logs`);
  return response.data;
}
