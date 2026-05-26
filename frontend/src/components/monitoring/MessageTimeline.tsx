import type { AgentMessage } from "@/types/message";
import { MessageSquare, ArrowRight } from "lucide-react";

interface MessageTimelineProps {
  messages: AgentMessage[];
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

export default function MessageTimeline({ messages }: MessageTimelineProps) {
  return (
    <div className="space-y-0">
      {messages.length === 0 && (
        <div className="text-slate-400 text-sm text-center py-8">
          No messages yet
        </div>
      )}
      {messages.map((msg, idx) => (
        <div key={msg.id} className="relative pl-8 pb-4">
          {/* Timeline line */}
          {idx < messages.length - 1 && (
            <div className="absolute left-[14px] top-8 w-0.5 h-full bg-slate-200" />
          )}
          {/* Timeline dot */}
          <div className="absolute left-1.5 top-1.5 w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center">
            <MessageSquare className="w-3 h-3 text-blue-600" />
          </div>
          {/* Content */}
          <div className="bg-white border border-slate-200 rounded-lg p-3">
            <div className="flex items-center gap-1 text-xs text-slate-500 mb-1.5">
              <span className="font-semibold text-emerald-700">
                {msg.from_agent}
              </span>
              <ArrowRight className="w-3 h-3" />
              <span className="font-semibold text-blue-700">
                {msg.to_agent}
              </span>
              <span className="ml-auto">{formatTime(msg.created_at)}</span>
            </div>
            <p className="text-sm text-slate-700 whitespace-pre-wrap">
              {msg.content.length > 300
                ? msg.content.slice(0, 300) + "..."
                : msg.content}
            </p>
            {msg.message_type !== "text" && (
              <span className="inline-block mt-1.5 badge-gray">
                {msg.message_type}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
