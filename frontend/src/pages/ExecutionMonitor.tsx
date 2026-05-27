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
import { ArrowLeft, RefreshCw, Terminal, MessageSquare } from "lucide-react";
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
import type { Execution, ExecutionLog } from "@/types/execution";
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
    addLog,
    addMessage,
    updateExecutionStatus,
    updateExecutionTokens,
  } = useExecutionStore();
  const { fetchWorkflow } = useWorkflowStore();

  const [graphNodes, setGraphNodes] = useState<Node[]>([]);
  const [graphEdges, setGraphEdges] = useState<Edge[]>([]);
  const [activeTab, setActiveTab] = useState<"chat" | "logs">("chat");

  const isRunning =
    activeExecution?.status === "running" ||
    activeExecution?.status === "pending";

  const userQuery =
    (activeExecution?.input_data?.query as string) ||
    (activeExecution?.input_data?.message as string) ||
    (activeExecution?.input_data?.input as string) ||
    "";

  const finalOutput = activeExecution?.output_data?.final_output as
    | string
    | undefined;

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
          const isCurrentNode = n.id === activeExecution.current_node;
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
      } else if (type === "agent_message") {
        addMessage({
          id: crypto.randomUUID(),
          execution_id: id,
          from_agent: (data.agent_name as string) || "unknown",
          to_agent: "workflow",
          content: (data.content as string) || "",
          message_type: "text",
          metadata: {
            node_id: data.node_id,
            prompt_tokens: data.prompt_tokens,
            completion_tokens: data.completion_tokens,
          },
          created_at: new Date().toISOString(),
        });
      } else if (type === "status") {
        updateExecutionStatus(
          id,
          data.status as Execution["status"],
          data.current_node as string | null
        );
        const tokenUpdate: Partial<Execution> = {};
        if (data.total_tokens !== undefined)
          tokenUpdate.total_tokens = data.total_tokens as number;
        if (data.prompt_tokens !== undefined)
          tokenUpdate.prompt_tokens = data.prompt_tokens as number;
        if (data.completion_tokens !== undefined)
          tokenUpdate.completion_tokens = data.completion_tokens as number;
        if (data.estimated_cost_usd !== undefined)
          tokenUpdate.estimated_cost_usd = data.estimated_cost_usd as number;
        if (Object.keys(tokenUpdate).length > 0) {
          updateExecutionTokens(id, tokenUpdate);
        }
      } else if (type === "step_completed" || type === "node_started" || type === "node_completed") {
        updateExecutionStatus(id, "running", data.node_id as string);
      } else if (type === "execution_completed") {
        updateExecutionStatus(id, "completed", null);
        fetchExecution(id);
        fetchExecutionLogs(id);
        fetchExecutionMessages(id);
      } else if (type === "execution_failed") {
        updateExecutionStatus(id, "failed", null);
        fetchExecution(id);
        fetchExecutionLogs(id);
        fetchExecutionMessages(id);
      }
    },
    [
      id,
      addLog,
      addMessage,
      updateExecutionStatus,
      updateExecutionTokens,
      fetchExecution,
      fetchExecutionLogs,
      fetchExecutionMessages,
    ]
  );

  useWebSocket({
    url: `/ws/executions/${id}`,
    onMessage: onWsMessage,
    autoConnect: !!id,
  });

  // Polling fallback
  useEffect(() => {
    if (!id || !isRunning) return;
    const interval = setInterval(() => {
      fetchExecutionLogs(id);
      fetchExecutionMessages(id);
      fetchExecution(id);
    }, 3000);
    return () => clearInterval(interval);
  }, [
    id,
    isRunning,
    fetchExecutionLogs,
    fetchExecutionMessages,
    fetchExecution,
  ]);

  function handleRefresh() {
    if (!id) return;
    fetchExecution(id);
    fetchExecutionLogs(id);
    fetchExecutionMessages(id);
  }

  const statusLabel = activeExecution?.status || "loading";

  function getStatusBadge(status: string) {
    const styles: Record<string, string> = {
      completed: "bg-emerald-100 text-emerald-700",
      failed: "bg-red-100 text-red-700",
      running: "bg-blue-100 text-blue-700",
      pending: "bg-slate-100 text-slate-600",
      cancelled: "bg-amber-100 text-amber-700",
    };
    return styles[status] || "bg-slate-100 text-slate-600";
  }

  return (
    <div className="h-[calc(100vh-2rem)] -m-8 flex flex-col">
      {/* Header bar */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-slate-200">
        <div className="flex items-center gap-4">
          <button
            className="btn-ghost"
            onClick={() => navigate("/executions")}
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-900">
                Execution Monitor
              </h2>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(statusLabel)}`}
              >
                {isRunning && (
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                )}
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
        </div>
      </div>

      {/* Main area: Chat (center) + Sidebars */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar: Workflow Graph + Token Tracker */}
        <div className="w-72 bg-white border-r border-slate-200 flex flex-col">
          {/* Mini workflow graph */}
          <div className="h-52 border-b border-slate-200">
            <ReactFlow
              nodes={graphNodes}
              edges={graphEdges}
              nodeTypes={nodeTypes}
              fitView
              nodesDraggable={false}
              nodesConnectable={false}
              elementsSelectable={false}
              panOnDrag={false}
              zoomOnScroll={false}
              zoomOnPinch={false}
              zoomOnDoubleClick={false}
              preventScrolling={false}
              proOptions={{ hideAttribution: true }}
            >
              <Background
                variant={BackgroundVariant.Dots}
                gap={16}
                size={1}
              />
            </ReactFlow>
          </div>

          {/* Token/Cost Tracker */}
          <div className="p-4 flex-1 overflow-y-auto">
            <TokenCostTracker
              promptTokens={activeExecution?.prompt_tokens || 0}
              completionTokens={activeExecution?.completion_tokens || 0}
              totalTokens={activeExecution?.total_tokens || 0}
              estimatedCostUsd={activeExecution?.estimated_cost_usd || 0}
            />

            {/* Current node indicator */}
            {activeExecution?.current_node && isRunning && (
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs font-medium text-blue-700">
                  Currently executing
                </p>
                <p className="text-sm font-semibold text-blue-900 mt-0.5">
                  {activeExecution.current_node}
                </p>
              </div>
            )}

            {/* Error display */}
            {activeExecution?.error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-xs font-medium text-red-700">Error</p>
                <p className="text-sm text-red-800 mt-0.5">
                  {activeExecution.error}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Center: Chat / Logs with tab switcher */}
        <div className="flex-1 flex flex-col bg-slate-50">
          {/* Tab bar */}
          <div className="flex items-center gap-1 px-4 pt-3 pb-0">
            <button
              onClick={() => setActiveTab("chat")}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-sm font-medium transition-colors ${
                activeTab === "chat"
                  ? "bg-white text-slate-900 border border-b-0 border-slate-200"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              Chat ({messages.length})
            </button>
            <button
              onClick={() => setActiveTab("logs")}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-sm font-medium transition-colors ${
                activeTab === "logs"
                  ? "bg-white text-slate-900 border border-b-0 border-slate-200"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <Terminal className="w-4 h-4" />
              Logs ({logs.length})
            </button>
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-hidden bg-white border-t border-slate-200 mx-4 mb-4 rounded-b-lg rounded-tr-lg border-x">
            {activeTab === "chat" ? (
              <div className="h-full flex flex-col">
                <div className="flex-1 overflow-y-auto">
                  <MessageTimeline
                    messages={messages}
                    userQuery={userQuery}
                  />
                </div>

                {/* Final output banner */}
                {finalOutput && !isRunning && (
                  <div className="border-t border-slate-200 p-4 bg-emerald-50">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium">
                        Final Output
                      </span>
                    </div>
                    <div className="text-sm text-slate-800 whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed">
                      {finalOutput.length > 2000
                        ? finalOutput.slice(0, 2000) + "..."
                        : finalOutput}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full">
                <LogStream logs={logs} />
              </div>
            )}
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
