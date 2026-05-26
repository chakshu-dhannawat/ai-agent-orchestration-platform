import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Bot } from "lucide-react";

interface AgentNodeData {
  label: string;
  agentName?: string;
  agentRole?: string;
  agentModel?: string;
  [key: string]: unknown;
}

function AgentNode({ data, selected }: NodeProps) {
  const nodeData = data as unknown as AgentNodeData;
  return (
    <div
      className={`px-4 py-3 rounded-xl bg-white border-2 shadow-sm min-w-[180px] ${
        selected ? "border-blue-500 shadow-blue-100" : "border-slate-200"
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-blue-500 !border-2 !border-white"
      />
      <div className="flex items-start gap-3">
        <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-lg shrink-0 mt-0.5">
          <Bot className="w-4 h-4 text-blue-600" />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-900 truncate">
            {nodeData.agentName || nodeData.label || "Agent"}
          </p>
          {nodeData.agentRole && (
            <p className="text-xs text-slate-500 truncate">{nodeData.agentRole}</p>
          )}
          {nodeData.agentModel && (
            <span className="inline-block mt-1 px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-mono">
              {nodeData.agentModel}
            </span>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-blue-500 !border-2 !border-white"
      />
    </div>
  );
}

export default memo(AgentNode);
