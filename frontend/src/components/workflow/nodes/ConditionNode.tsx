import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { GitBranch } from "lucide-react";

interface ConditionNodeData {
  label: string;
  condition?: string;
  [key: string]: unknown;
}

function ConditionNode({ data, selected }: NodeProps) {
  const nodeData = data as unknown as ConditionNodeData;
  return (
    <div className="relative">
      {/* Diamond shape via rotated square */}
      <div
        className={`w-[120px] h-[120px] rotate-45 rounded-lg border-2 shadow-sm ${
          selected
            ? "border-amber-500 bg-amber-50 shadow-amber-100"
            : "border-amber-300 bg-amber-50"
        }`}
      />
      {/* Content overlay (not rotated) */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <GitBranch className="w-4 h-4 text-amber-600 mb-1" />
        <p className="text-xs font-semibold text-amber-900 text-center px-2 max-w-[100px] truncate">
          {nodeData.label || "Condition"}
        </p>
        {nodeData.condition && (
          <p className="text-[10px] text-amber-600 text-center px-2 max-w-[100px] truncate mt-0.5">
            {nodeData.condition}
          </p>
        )}
      </div>
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-amber-500 !border-2 !border-white !top-[-6px]"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="default"
        className="!w-3 !h-3 !bg-amber-500 !border-2 !border-white !bottom-[-6px]"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="alternate"
        className="!w-3 !h-3 !bg-amber-500 !border-2 !border-white !right-[-6px]"
      />
    </div>
  );
}

export default memo(ConditionNode);
