import { Routes, Route } from "react-router-dom";
import Layout from "@/components/layout/Layout";
import Dashboard from "@/pages/Dashboard";
import AgentList from "@/pages/AgentList";
import AgentDetail from "@/pages/AgentDetail";
import WorkflowList from "@/pages/WorkflowList";
import WorkflowBuilder from "@/pages/WorkflowBuilder";
import ExecutionList from "@/pages/ExecutionList";
import ExecutionMonitor from "@/pages/ExecutionMonitor";
import TemplateGallery from "@/pages/TemplateGallery";
import ChannelList from "@/pages/ChannelList";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/agents" element={<AgentList />} />
        <Route path="/agents/new" element={<AgentDetail />} />
        <Route path="/agents/:id" element={<AgentDetail />} />
        <Route path="/workflows" element={<WorkflowList />} />
        <Route path="/workflows/new" element={<WorkflowBuilder />} />
        <Route path="/workflows/:id" element={<WorkflowBuilder />} />
        <Route path="/executions" element={<ExecutionList />} />
        <Route path="/executions/:id" element={<ExecutionMonitor />} />
        <Route path="/templates" element={<TemplateGallery />} />
        <Route path="/channels" element={<ChannelList />} />
      </Routes>
    </Layout>
  );
}

export default App;
