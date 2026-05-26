export interface AgentMessage {
  id: string;
  execution_id: string;
  from_agent: string;
  to_agent: string;
  content: string;
  message_type: string;
  metadata: Record<string, unknown>;
  created_at: string;
}
