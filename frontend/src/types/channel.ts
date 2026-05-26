export interface Channel {
  id: string;
  type: string;
  name: string;
  config: Record<string, unknown>;
  agent_id: string | null;
  workflow_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ChannelCreate {
  type: string;
  name: string;
  config?: Record<string, unknown>;
  agent_id?: string | null;
  workflow_id?: string | null;
  is_active?: boolean;
}
