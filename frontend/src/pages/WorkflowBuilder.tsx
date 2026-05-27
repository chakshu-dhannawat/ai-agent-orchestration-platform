import { useCallback, useEffect, useMemo, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ReactFlow,
  Controls,
  Background,
  BackgroundVariant,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Save,
  Play,
  CheckCircle,
  Bot,
  GitBranch,
  CirclePlay,
  CircleStop,
  X,
  GripVertical,
} from "lucide-react";
import Header from "@/components/layout/Header";
import AgentNode from "@/components/workflow/nodes/AgentNode";
import ConditionNode from "@/components/workflow/nodes/ConditionNode";
import StartNode from "@/components/workflow/nodes/StartNode";
import EndNode from "@/components/workflow/nodes/EndNode";
import { useWorkflowStore } from "@/store/workflowStore";
import { useExecutionStore } from "@/store/executionStore";
import { useAgentStore } from "@/store/agentStore";

const nodeTypes = {
  agent: AgentNode,
  condition: ConditionNode,
  start: StartNode,
  end: EndNode,
};

const toolboxItems = [
  {
    type: "agent",
    label: "Agent Node",
    icon: Bot,
    color: "bg-blue-100 text-blue-600",
  },
  {
    type: "condition",
    label: "Condition",
    icon: GitBranch,
    color: "bg-amber-100 text-amber-600",
  },
  {
    type: "start",
    label: "Start",
    icon: CirclePlay,
    color: "bg-emerald-100 text-emerald-600",
  },
  {
    type: "end",
    label: "End",
    icon: CircleStop,
    color: "bg-red-100 text-red-600",
  },
];

let nodeIdCounter = 0;
function getNextId() {
  return `node_${++nodeIdCounter}`;
}

function WorkflowBuilderInner() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { fetchWorkflow, createWorkflow, updateWorkflow, validateWorkflow } =
    useWorkflowStore();
  const { startExecution } = useExecutionStore();
  const { agents, fetchAgents } = useAgentStore();

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [workflowName, setWorkflowName] = useState("Untitled Workflow");
  const [workflowDescription, setWorkflowDescription] = useState("");
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [saving, setSaving] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    errors: string[];
  } | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  useEffect(() => {
    if (id) {
      fetchWorkflow(id).then((wf) => {
        setWorkflowName(wf.name);
        setWorkflowDescription(wf.description);
        const graph = wf.graph_definition;
        if (graph?.nodes) {
          setNodes(graph.nodes as Node[]);
          nodeIdCounter = graph.nodes.length + 10;
        }
        if (graph?.edges) {
          setEdges(graph.edges as Edge[]);
        }
      });
    }
  }, [id, fetchWorkflow, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge({ ...params, animated: true }, eds)
      );
    },
    [setEdges]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node);
    },
    []
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  function handleDragStart(
    e: React.DragEvent<HTMLDivElement>,
    nodeType: string
  ) {
    e.dataTransfer.setData("application/reactflow", nodeType);
    e.dataTransfer.effectAllowed = "move";
  }

  const onDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const type = e.dataTransfer.getData("application/reactflow");
      if (!type) return;

      const wrapperBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const position = {
        x: e.clientX - (wrapperBounds?.left || 0) - 75,
        y: e.clientY - (wrapperBounds?.top || 0) - 25,
      };

      const newNode: Node = {
        id: getNextId(),
        type,
        position,
        data: {
          label:
            type === "start"
              ? "Start"
              : type === "end"
                ? "End"
                : type === "condition"
                  ? "Condition"
                  : "New Agent",
        },
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes]
  );

  function updateNodeData(nodeId: string, data: Record<string, unknown>) {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n
      )
    );
    if (selectedNode?.id === nodeId) {
      setSelectedNode((prev) =>
        prev ? { ...prev, data: { ...prev.data, ...data } } : null
      );
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      const graph_definition = { nodes, edges };
      if (id) {
        await updateWorkflow(id, {
          name: workflowName,
          description: workflowDescription,
          graph_definition,
        });
      } else {
        const wf = await createWorkflow({
          name: workflowName,
          description: workflowDescription,
          graph_definition,
        });
        navigate(`/workflows/${wf.id}`, { replace: true });
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleValidate() {
    if (!id) {
      setValidationResult({
        valid: false,
        errors: ["Save the workflow first to validate"],
      });
      return;
    }
    try {
      const result = await validateWorkflow(id);
      setValidationResult(result);
    } catch {
      setValidationResult({
        valid: false,
        errors: ["Validation request failed"],
      });
    }
  }

  async function handleRun() {
    if (!id) return;
    setRunError(null);

    const userInput = window.prompt("Enter your query:");
    if (userInput === null) return;

    try {
      const exec = await startExecution({
        workflow_id: id,
        input_data: { query: userInput },
      });
      navigate(`/executions/${exec.id}`);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to start execution";
      setRunError(message);
    }
  }

  const nodeTypesStable = useMemo(() => nodeTypes, []);

  return (
    <div className="h-[calc(100vh-2rem)] -m-8 flex flex-col">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-slate-200">
        <div className="flex items-center gap-4">
          <button
            className="btn-ghost"
            onClick={() => navigate("/workflows")}
          >
            <X className="w-4 h-4" />
          </button>
          <div>
            <input
              className="text-lg font-semibold text-slate-900 bg-transparent border-none outline-none focus:ring-0 p-0"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              placeholder="Workflow name"
            />
            <input
              className="block text-xs text-slate-400 bg-transparent border-none outline-none focus:ring-0 p-0 mt-0.5 w-64"
              value={workflowDescription}
              onChange={(e) => setWorkflowDescription(e.target.value)}
              placeholder="Add a description..."
            />
          </div>
        </div>
        <div className="flex items-center gap-2">
          {runError && (
            <span className="text-xs mr-2 text-red-600 flex items-center gap-1">
              {runError}
              <button
                className="p-0.5 rounded hover:bg-red-100"
                onClick={() => setRunError(null)}
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          )}
          {validationResult && (
            <span
              className={`text-xs mr-2 ${
                validationResult.valid ? "text-emerald-600" : "text-red-600"
              }`}
            >
              {validationResult.valid
                ? "Valid"
                : validationResult.errors[0]}
            </span>
          )}
          <button className="btn-secondary" onClick={handleValidate}>
            <CheckCircle className="w-4 h-4" />
            Validate
          </button>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            <Save className="w-4 h-4" />
            {saving ? "Saving..." : "Save"}
          </button>
          {id && (
            <button className="btn-primary bg-emerald-600 hover:bg-emerald-700" onClick={handleRun}>
              <Play className="w-4 h-4" />
              Run
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Toolbox */}
        <div className="w-56 bg-white border-r border-slate-200 p-4 space-y-2">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
            Node Types
          </h3>
          {toolboxItems.map((item) => (
            <div
              key={item.type}
              draggable
              onDragStart={(e) => handleDragStart(e, item.type)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg border border-slate-200 cursor-grab hover:border-slate-300 hover:shadow-sm transition-all active:cursor-grabbing"
            >
              <GripVertical className="w-3.5 h-3.5 text-slate-300" />
              <div
                className={`flex items-center justify-center w-7 h-7 rounded ${item.color}`}
              >
                <item.icon className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium text-slate-700">
                {item.label}
              </span>
            </div>
          ))}
        </div>

        {/* Canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypesStable}
            fitView
            deleteKeyCode={["Backspace", "Delete"]}
          >
            <Controls />
            <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
          </ReactFlow>
        </div>

        {/* Right Config Drawer */}
        {selectedNode && (
          <div className="w-72 bg-white border-l border-slate-200 p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-900">
                Node Configuration
              </h3>
              <button
                className="p-1 rounded hover:bg-slate-100 text-slate-400"
                onClick={() => setSelectedNode(null)}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="label">Node ID</label>
                <p className="text-xs text-slate-500 font-mono">
                  {selectedNode.id}
                </p>
              </div>

              <div>
                <label className="label">Type</label>
                <span className="badge-blue">{selectedNode.type}</span>
              </div>

              {(selectedNode.type === "agent" ||
                selectedNode.type === "condition") && (
                <div>
                  <label className="label">Label</label>
                  <input
                    className="input"
                    value={(selectedNode.data?.label as string) || ""}
                    onChange={(e) =>
                      updateNodeData(selectedNode.id, {
                        label: e.target.value,
                      })
                    }
                  />
                </div>
              )}

              {selectedNode.type === "agent" && (
                <>
                  <div>
                    <label className="label">Linked Agent</label>
                    <select
                      className="select"
                      value={(selectedNode.data?.agentId as string) || ""}
                      onChange={(e) => {
                        const agent = agents.find(
                          (a) => a.id === e.target.value
                        );
                        updateNodeData(selectedNode.id, {
                          agentId: e.target.value,
                          agentName: agent?.name || "",
                          agentRole: agent?.role || "",
                          agentModel: agent?.model || "",
                          label: agent?.name || "Agent",
                        });
                      }}
                    >
                      <option value="">Select an agent...</option>
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name} ({a.role})
                        </option>
                      ))}
                    </select>
                  </div>
                  {(selectedNode.data as Record<string, unknown>)?.agentModel && (
                    <div>
                      <label className="label">Model</label>
                      <p className="text-sm text-slate-600 font-mono">
                        {(selectedNode.data as Record<string, unknown>).agentModel as string}
                      </p>
                    </div>
                  )}
                </>
              )}

              {selectedNode.type === "condition" && (
                <div>
                  <label className="label">Condition Expression</label>
                  <textarea
                    className="textarea text-sm"
                    rows={3}
                    placeholder="e.g., output.confidence > 0.8"
                    value={
                      ((selectedNode.data as Record<string, unknown>)?.condition as string) || ""
                    }
                    onChange={(e) =>
                      updateNodeData(selectedNode.id, {
                        condition: e.target.value,
                      })
                    }
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    Default path = bottom, alternate = right
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WorkflowBuilder() {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderInner />
    </ReactFlowProvider>
  );
}
