import { useEffect, useCallback, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  type Node,
  type Edge,
  ReactFlowProvider,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { StopCircle, ArrowLeft, RefreshCw } from "lucide-react";
import Header from "@/components/layout/Header";
import LogStream from "@/components/monitoring/LogStream";
import MessageTimeline from "@/components/monitoring/MessageTimeline";
import TokenCostTracker from "@/components/monitoring/TokenCostTracker";
import AgentNode from "@/components/workflow/nodes/AgentNode";
import ConditionNode from "@/components/workflow/nodes/ConditionNode";
import StartNode from "@/components/workflow/nodes/StartNode";
import EndNode from "@/components/workflow/nodes/EndNode";
import { useExecutionStore } from "@/store/executionStore";
import { useWorkflowStore } from "@/store/workflowStore";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { ExecutionLog } from "@/types/execution";
import type { AgentMessage } from "@/types/message";

const nodeTypes = {
  agent: AgentNode,
  condition: ConditionNode,
  start: StartNode,
  end: EndNode,
};

function ExecutionMonitorInner() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    activeExecution,
    logs,
    messages,
    fetchExecution,
    fetchExecutionLogs,
    fetchExecutionMessages,
    cancelExecution,
    addLog,
    addMessage,
    updateExecutionStatus,
  } = useExecutionStore();
  const { fetchWorkflow } = useWorkflowStore();

  const [graphNodes, setGraphNodes] = useState<Node[]>([]);
  const [graphEdges, setGraphEdges] = useState<Edge[]>([]);
  const [cancelling, setCancelling] = useState(false);

  // Load execution data
  useEffect(() => {
    if (!id) return;
    fetchExecution(id);
    fetchExecutionLogs(id);
    fetchExecutionMessages(id);
  }, [id, fetchExecution, fetchExecutionLogs, fetchExecutionMessages]);

  // Load workflow graph
  useEffect(() => {
    if (!activeExecution) return;
    fetchWorkflow(activeExecution.workflow_id).then((wf) => {
      const graph = wf.graph_definition;
      if (graph?.nodes) {
        const flowNodes = (graph.nodes as Node[]).map((n) => {
          const isCurrentNode =
            n.id === activeExecution.current_node;
          return {
            ...n,
            style: isCurrentNode
              ? {
                  boxShadow: "0 0 0 3px #3b82f6",
                  borderRadius: "12px",
                }
              : undefined,
          };
        });
        setGraphNodes(flowNodes);
      }
      if (graph?.edges) {
        setGraphEdges(graph.edges as Edge[]);
      }
    });
  }, [activeExecution, fetchWorkflow]);

  // WebSocket for real-time updates
  const onWsMessage = useCallback(
    (data: Record<string, unknown>) => {
      if (!id) return;
      const type = data.type as string;
      if (type === "log") {
        addLog(data.payload as ExecutionLog);
      } else if (type === "message") {
        addMessage(data.payload as AgentMessage);
      } else if (type === "status") {
        updateExecutionStatus(
          id,
          data.status as string,
          data.current_node as string | null
        );
      }
    },
    [id, addLog, addMessage, updateExecutionStatus]
  );

  useWebSocket({
    url: `/ws/executions/${id}`,
    onMessage: onWsMessage,
    autoConnect: !!id,
  });

  async function handleCancel() {
    if (!id || cancelling) return;
    setCancelling(true);
    try {
      await cancelExecution(id);
    } finally {
      setCancelling(false);
    }
  }

  function handleRefresh() {
    if (!id) return;
    fetchExecution(id);
    fetchExecutionLogs(id);
    fetchExecutionMessages(id);
  }

  const isRunning = activeExecution?.status === "running";
  const statusLabel = activeExecution?.status || "loading";

  function getStatusBadge(status: string): string {
    const map: Record<string, string> = {
      completed: "badge-green",
      failed: "badge-red",
      running: "badge-blue",
      pending: "badge-gray",
      cancelled: "badge-yellow",
    };
    return map[status] || "badge-gray";
  }

  return (
    <div className="h-[calc(100vh-2rem)] -m-8 flex flex-col">
      {/* Header bar */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-slate-200">
        <div className="flex items-center gap-4">
          <button className="btn-ghost" onClick={() => navigate("/executions")}>
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-900">
                Execution Monitor
              </h2>
              <span className={getStatusBadge(statusLabel)}>
                {statusLabel}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              {id?.slice(0, 12)}...
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-ghost" onClick={handleRefresh}>
            <RefreshCw className="w-4 h-4" />
          </button>
          {isRunning && (
            <button
              className="btn-danger"
              onClick={handleCancel}
              disabled={cancelling}
            >
              <StopCircle className="w-4 h-4" />
              {cancelling ? "Cancelling..." : "Cancel"}
            </button>
          )}
        </div>
      </div>

      {/* Three-panel layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Workflow Graph */}
        <div className="w-1/3 border-r border-slate-200">
          <ReactFlow
            nodes={graphNodes}
            edges={graphEdges}
            nodeTypes={nodeTypes}
            fitView
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            panOnDrag
            zoomOnScroll
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={16}
              size={1}
            />
          </ReactFlow>
        </div>

        {/* Center: Log Stream */}
        <div className="flex-1 flex flex-col border-r border-slate-200">
          <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Log Output
            </h3>
          </div>
          <div className="flex-1 overflow-hidden">
            <LogStream logs={logs} />
          </div>
        </div>

        {/* Right: Messages + Token Tracker */}
        <div className="w-80 flex flex-col overflow-hidden">
          {/* Token/Cost Tracker */}
          <div className="p-4 border-b border-slate-200">
            <TokenCostTracker
              promptTokens={activeExecution?.prompt_tokens || 0}
              completionTokens={activeExecution?.completion_tokens || 0}
              totalTokens={activeExecution?.total_tokens || 0}
              estimatedCostUsd={activeExecution?.estimated_cost_usd || 0}
            />
          </div>

          {/* Message Timeline */}
          <div className="flex-1 overflow-y-auto">
            <div className="px-4 py-2.5 border-b border-slate-200 sticky top-0 bg-white">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Agent Messages ({messages.length})
              </h3>
            </div>
            <div className="p-4">
              <MessageTimeline messages={messages} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ExecutionMonitor() {
  return (
    <ReactFlowProvider>
      <ExecutionMonitorInner />
    </ReactFlowProvider>
  );
}
