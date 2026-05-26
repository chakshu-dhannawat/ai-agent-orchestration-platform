import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Bot,
  GitBranch,
  Play,
  BookTemplate,
  Radio,
  Zap,
} from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "/agents", icon: Bot, label: "Agents" },
  { to: "/workflows", icon: GitBranch, label: "Workflows" },
  { to: "/executions", icon: Play, label: "Executions" },
  { to: "/templates", icon: BookTemplate, label: "Templates" },
  { to: "/channels", icon: Radio, label: "Channels" },
];

export default function Sidebar() {
  return (
    <aside className="w-[260px] min-w-[260px] h-screen bg-slate-900 flex flex-col">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800">
        <div className="flex items-center justify-center w-9 h-9 bg-blue-600 rounded-lg">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-white font-semibold text-base leading-tight">
            AI Orchestrator
          </h1>
          <p className="text-slate-500 text-xs">Agent Platform</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "active" : ""}`
            }
          >
            <item.icon className="w-5 h-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-emerald-500 rounded-full" />
          <span className="text-xs text-slate-400">System Online</span>
        </div>
      </div>
    </aside>
  );
}
