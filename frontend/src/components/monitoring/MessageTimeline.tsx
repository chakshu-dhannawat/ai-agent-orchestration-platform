import { useEffect, useRef } from "react";
import type { AgentMessage } from "@/types/message";
import { Bot, User, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface MessageTimelineProps {
  messages: AgentMessage[];
  userQuery?: string;
}

const AGENT_COLORS: Record<string, { bg: string; border: string; icon: string; name: string }> = {
  Researcher: { bg: "bg-blue-50", border: "border-blue-200", icon: "bg-blue-500", name: "text-blue-700" },
  Writer: { bg: "bg-violet-50", border: "border-violet-200", icon: "bg-violet-500", name: "text-violet-700" },
  Reviewer: { bg: "bg-amber-50", border: "border-amber-200", icon: "bg-amber-500", name: "text-amber-700" },
  "Triage Agent": { bg: "bg-emerald-50", border: "border-emerald-200", icon: "bg-emerald-500", name: "text-emerald-700" },
  "Billing Support Agent": { bg: "bg-pink-50", border: "border-pink-200", icon: "bg-pink-500", name: "text-pink-700" },
  "Technical Support Agent": { bg: "bg-cyan-50", border: "border-cyan-200", icon: "bg-cyan-500", name: "text-cyan-700" },
  "General Support Agent": { bg: "bg-slate-50", border: "border-slate-200", icon: "bg-slate-500", name: "text-slate-700" },
};

const DEFAULT_COLOR = { bg: "bg-gray-50", border: "border-gray-200", icon: "bg-gray-500", name: "text-gray-700" };

function getColor(agent: string) {
  return AGENT_COLORS[agent] || DEFAULT_COLOR;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function CollapsibleMessage({ content }: { content: string }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = content.length > 600;
  const display = isLong && !expanded ? content.slice(0, 600) : content;

  return (
    <div>
      <div className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
        {display}
        {isLong && !expanded && "..."}
      </div>
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 mt-2 text-xs font-medium text-blue-600 hover:text-blue-700"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-3 h-3" /> Show less
            </>
          ) : (
            <>
              <ChevronDown className="w-3 h-3" /> Show full output ({Math.ceil(content.length / 1000)}k chars)
            </>
          )}
        </button>
      )}
    </div>
  );
}

export default function MessageTimeline({ messages, userQuery }: MessageTimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div ref={containerRef} className="flex flex-col gap-4 overflow-y-auto h-full p-4">
      {/* User query bubble */}
      {userQuery && (
        <div className="flex gap-3 justify-end">
          <div className="max-w-[85%]">
            <div className="flex items-center gap-1.5 justify-end mb-1">
              <span className="text-xs font-semibold text-slate-600">You</span>
              <div className="w-5 h-5 rounded-full bg-slate-700 flex items-center justify-center">
                <User className="w-3 h-3 text-white" />
              </div>
            </div>
            <div className="bg-slate-800 text-white rounded-2xl rounded-tr-sm px-4 py-3">
              <p className="text-sm leading-relaxed">{userQuery}</p>
            </div>
          </div>
        </div>
      )}

      {messages.length === 0 && !userQuery && (
        <div className="text-slate-400 text-sm text-center py-12">
          <Bot className="w-8 h-8 mx-auto mb-2 text-slate-300" />
          Waiting for agent responses...
        </div>
      )}

      {messages.map((msg) => {
        const color = getColor(msg.from_agent);
        return (
          <div key={msg.id} className="flex gap-3">
            <div className={`w-8 h-8 rounded-full ${color.icon} flex items-center justify-center shrink-0 mt-1`}>
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="max-w-[85%] min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-bold ${color.name}`}>
                  {msg.from_agent}
                </span>
                <span className="text-[10px] text-slate-400">
                  {formatTime(msg.created_at)}
                </span>
              </div>
              <div className={`${color.bg} ${color.border} border rounded-2xl rounded-tl-sm px-4 py-3`}>
                <CollapsibleMessage content={msg.content} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
