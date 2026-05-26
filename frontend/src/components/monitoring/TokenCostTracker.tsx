import { Coins, Zap, ArrowUpRight, ArrowDownLeft } from "lucide-react";

interface TokenCostTrackerProps {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  estimatedCostUsd: number;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toLocaleString();
}

export default function TokenCostTracker({
  promptTokens,
  completionTokens,
  totalTokens,
  estimatedCostUsd,
}: TokenCostTrackerProps) {
  return (
    <div className="space-y-3">
      {/* Total tokens */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
            Total Tokens
          </span>
        </div>
        <p className="text-2xl font-bold text-slate-900">
          {formatNumber(totalTokens)}
        </p>
      </div>

      {/* Prompt / Completion breakdown */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white border border-slate-200 rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <ArrowUpRight className="w-3.5 h-3.5 text-emerald-600" />
            <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
              Prompt
            </span>
          </div>
          <p className="text-lg font-semibold text-slate-900">
            {formatNumber(promptTokens)}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <ArrowDownLeft className="w-3.5 h-3.5 text-violet-600" />
            <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
              Completion
            </span>
          </div>
          <p className="text-lg font-semibold text-slate-900">
            {formatNumber(completionTokens)}
          </p>
        </div>
      </div>

      {/* Cost */}
      <div className="bg-slate-900 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-1">
          <Coins className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            Estimated Cost
          </span>
        </div>
        <p className="text-2xl font-bold text-white">
          ${estimatedCostUsd.toFixed(4)}
        </p>
      </div>
    </div>
  );
}
