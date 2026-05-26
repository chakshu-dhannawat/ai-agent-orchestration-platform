export interface WorkflowNode {
  id: string;
  type: "agent" | "condition" | "start" | "end";
  position: { x: number; y: number };
  data: {
    label: string;
    agentId?: string;
    agentName?: string;
    agentRole?: string;
    agentModel?: string;
    condition?: string;
    [key: string]: unknown;
  };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
  animated?: boolean;
}

export interface GraphDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  is_template: boolean;
  template_id: string | null;
  graph_definition: GraphDefinition;
  created_at: string;
  updated_at: string;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  is_template?: boolean;
  template_id?: string | null;
  graph_definition?: GraphDefinition;
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  is_template?: boolean;
  graph_definition?: GraphDefinition;
}
