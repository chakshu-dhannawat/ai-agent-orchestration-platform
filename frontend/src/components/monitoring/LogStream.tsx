import { useEffect, useRef } from "react";
import type { ExecutionLog } from "@/types/execution";

interface LogStreamProps {
  logs: ExecutionLog[];
  autoScroll?: boolean;
}

function getLevelClass(level: string): string {
  switch (level.toLowerCase()) {
    case "info":
      return "log-info";
    case "warning":
    case "warn":
      return "log-warn";
    case "error":
      return "log-error";
    case "debug":
      return "log-debug";
    default:
      return "text-slate-300";
  }
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function LogStream({ logs, autoScroll = true }: LogStreamProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  return (
    <div ref={containerRef} className="log-stream h-full overflow-y-auto">
      {logs.length === 0 && (
        <div className="text-slate-600 text-center py-8">
          Waiting for log output...
        </div>
      )}
      {logs.map((log) => (
        <div key={log.id} className="flex gap-2 py-0.5 leading-relaxed">
          <span className="log-timestamp shrink-0">
            [{formatTimestamp(log.created_at)}]
          </span>
          <span className={`shrink-0 uppercase w-14 ${getLevelClass(log.level)}`}>
            {log.level.toUpperCase().padEnd(5)}
          </span>
          {log.agent_name && (
            <span className="log-agent shrink-0">[{log.agent_name}]</span>
          )}
          <span className="text-slate-200 break-all">{log.message}</span>
        </div>
      ))}
    </div>
  );
}
