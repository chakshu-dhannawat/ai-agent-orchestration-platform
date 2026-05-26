import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Play } from "lucide-react";

function StartNode({ selected }: NodeProps) {
  return (
    <div
      className={`flex items-center justify-center w-16 h-16 rounded-full border-2 shadow-sm ${
        selected
          ? "border-emerald-600 bg-emerald-500 shadow-emerald-200"
          : "border-emerald-500 bg-emerald-500"
      }`}
    >
      <Play className="w-5 h-5 text-white ml-0.5" fill="currentColor" />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-white !border-2 !border-emerald-500"
      />
    </div>
  );
}

export default memo(StartNode);
