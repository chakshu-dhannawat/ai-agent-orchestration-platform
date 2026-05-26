export interface Agent {
  id: string;
  name: string;
  role: string;
  system_prompt: string;
  model: string;
  tools: string[];
  channels: string[];
  schedule: Record<string, string> | null;
  memory_enabled: boolean;
  memory_window: number;
  skills: string[];
  interaction_rules: Record<string, unknown>;
  guardrails: Record<string, unknown>;
  temperature: number;
  max_tokens: number;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  role: string;
  system_prompt?: string;
  model?: string;
  tools?: string[];
  channels?: string[];
  schedule?: Record<string, string> | null;
  memory_enabled?: boolean;
  memory_window?: number;
  skills?: string[];
  interaction_rules?: Record<string, unknown>;
  guardrails?: Record<string, unknown>;
  temperature?: number;
  max_tokens?: number;
}

export interface AgentUpdate {
  name?: string;
  role?: string;
  system_prompt?: string;
  model?: string;
  tools?: string[];
  channels?: string[];
  schedule?: Record<string, string> | null;
  memory_enabled?: boolean;
  memory_window?: number;
  skills?: string[];
  interaction_rules?: Record<string, unknown>;
  guardrails?: Record<string, unknown>;
  temperature?: number;
  max_tokens?: number;
}
