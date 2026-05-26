import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Square } from "lucide-react";

function EndNode({ selected }: NodeProps) {
  return (
    <div
      className={`flex items-center justify-center w-16 h-16 rounded-full border-2 shadow-sm ${
        selected
          ? "border-red-600 bg-red-500 shadow-red-200"
          : "border-red-500 bg-red-500"
      }`}
    >
      <Square className="w-4 h-4 text-white" fill="currentColor" />
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-white !border-2 !border-red-500"
      />
    </div>
  );
}

export default memo(EndNode);
