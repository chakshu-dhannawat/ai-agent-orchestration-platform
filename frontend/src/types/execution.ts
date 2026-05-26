export type ExecutionStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface Execution {
  id: string;
  workflow_id: string;
  status: ExecutionStatus;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number;
  current_node: string | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ExecutionLog {
  id: string;
  execution_id: string;
  level: string;
  node_id: string | null;
  agent_name: string | null;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ExecutionCreate {
  workflow_id: string;
  input_data?: Record<string, unknown>;
}
