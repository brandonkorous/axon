import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AchievementsView } from "./components/Achievements/AchievementsView";
import { AuditLogView } from "./components/AuditLog/AuditLogView";
import { AxonView } from "./components/AxonView/AxonView";
import { HuddleView } from "./components/Huddle/HuddleView";
import { AgentView } from "./components/Conversation/AgentView";
import { DashboardView } from "./components/Dashboard/DashboardView";
import { IssueListView } from "./components/Issues/IssueListView";
import { MindView } from "./components/Mind/MindView";
import { OrgChartView } from "./components/OrgChart/OrgChartView";
import { TaskBoardView } from "./components/Tasks/TaskBoardView";
import { UsageView } from "./components/Usage/UsageView";
import { ApprovalsView } from "./components/Approvals/ApprovalsView";
import { InboxView } from "./components/Inbox/InboxView";
import { WorkerListView } from "./components/Workers/WorkerListView";
import { WorkerDetailView } from "./components/Workers/WorkerDetailView";
import { WorkerSetupView } from "./components/Workers/WorkerSetupView";
import { DocumentView } from "./components/Documents/DocumentView";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<AxonView />} />
        <Route path="/huddle" element={<HuddleView />} />
        <Route path="/agent/:agentId" element={<AgentView />} />
        <Route path="/dashboard" element={<DashboardView />} />
        <Route path="/tasks" element={<TaskBoardView />} />
        <Route path="/inbox" element={<InboxView />} />
        <Route path="/approvals" element={<ApprovalsView />} />
        <Route path="/issues" element={<IssueListView />} />
        <Route path="/achievements" element={<AchievementsView />} />
        <Route path="/org-chart" element={<OrgChartView />} />
        <Route path="/audit" element={<AuditLogView />} />
        <Route path="/usage" element={<UsageView />} />
        <Route path="/mind/:agentId?" element={<MindView />} />
        <Route path="/memory/:agentId?" element={<MindView />} />
        <Route path="/workers" element={<WorkerListView />} />
        <Route path="/workers/new" element={<WorkerSetupView />} />
        <Route path="/workers/:agentId" element={<WorkerDetailView />} />
        <Route path="/docs/:vaultId/*" element={<DocumentView />} />
      </Route>
    </Routes>
  );
}
