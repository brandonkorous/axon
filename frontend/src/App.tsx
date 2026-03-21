import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AxonView } from "./components/AxonView/AxonView";
import { BoardroomView } from "./components/Boardroom/BoardroomView";
import { AgentView } from "./components/Conversation/AgentView";
import { DashboardView } from "./components/Dashboard/DashboardView";
import { MemoryBrowserView } from "./components/MemoryBrowser/MemoryBrowserView";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<AxonView />} />
        <Route path="/boardroom" element={<BoardroomView />} />
        <Route path="/agent/:agentId" element={<AgentView />} />
        <Route path="/dashboard" element={<DashboardView />} />
        <Route path="/memory/:agentId?" element={<MemoryBrowserView />} />
      </Route>
    </Routes>
  );
}
