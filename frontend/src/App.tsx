import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";

const AchievementsView = lazy(() => import("./components/Achievements/AchievementsView").then(m => ({ default: m.AchievementsView })));
const AuditLogView = lazy(() => import("./components/AuditLog/AuditLogView").then(m => ({ default: m.AuditLogView })));
const AxonView = lazy(() => import("./components/AxonView/AxonView").then(m => ({ default: m.AxonView })));
const HuddleView = lazy(() => import("./components/Huddle/HuddleView").then(m => ({ default: m.HuddleView })));
const AgentView = lazy(() => import("./components/Conversation/AgentView").then(m => ({ default: m.AgentView })));
const DashboardView = lazy(() => import("./components/Dashboard/DashboardView").then(m => ({ default: m.DashboardView })));
const IssueListView = lazy(() => import("./components/Issues/IssueListView").then(m => ({ default: m.IssueListView })));
const MindView = lazy(() => import("./components/Mind/MindView").then(m => ({ default: m.MindView })));
const OrgChartView = lazy(() => import("./components/OrgChart/OrgChartView").then(m => ({ default: m.OrgChartView })));
const TaskBoardView = lazy(() => import("./components/Tasks/TaskBoardView").then(m => ({ default: m.TaskBoardView })));
const UsageView = lazy(() => import("./components/Usage/UsageView").then(m => ({ default: m.UsageView })));
const ApprovalsView = lazy(() => import("./components/Approvals/ApprovalsView").then(m => ({ default: m.ApprovalsView })));
const DocumentView = lazy(() => import("./components/Documents/DocumentView").then(m => ({ default: m.DocumentView })));
const PluginBrowser = lazy(() => import("./components/Plugins/PluginBrowser").then(m => ({ default: m.PluginBrowser })));
const PluginCreateView = lazy(() => import("./components/Plugins/PluginCreateView").then(m => ({ default: m.PluginCreateView })));
const SkillBrowser = lazy(() => import("./components/Skills/SkillBrowser").then(m => ({ default: m.SkillBrowser })));
const SkillCreateView = lazy(() => import("./components/Skills/SkillCreateView").then(m => ({ default: m.SkillCreateView })));
const ArtifactViewer = lazy(() => import("./components/Artifacts/ArtifactViewer").then(m => ({ default: m.ArtifactViewer })));
const SandboxImagesView = lazy(() => import("./components/Sandbox/SandboxImagesView").then(m => ({ default: m.SandboxImagesView })));
const GitRepoList = lazy(() => import("./components/GitRepos/GitRepoList").then(m => ({ default: m.GitRepoList })));
const AnalyticsView = lazy(() => import("./components/Analytics/AnalyticsView").then(m => ({ default: m.AnalyticsView })));
const CalendarView = lazy(() => import("./components/Calendar/CalendarView").then(m => ({ default: m.CalendarView })));

export default function App() {
  return (
    <Suspense>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<AxonView />} />
          <Route path="/huddle" element={<HuddleView />} />
          <Route path="/agent/:agentId" element={<AgentView />} />
          <Route path="/dashboard" element={<DashboardView />} />
          <Route path="/tasks" element={<TaskBoardView />} />
          <Route path="/calendar" element={<CalendarView />} />
          <Route path="/approvals" element={<ApprovalsView />} />
          <Route path="/issues" element={<IssueListView />} />
          <Route path="/achievements" element={<AchievementsView />} />
          <Route path="/org-chart" element={<OrgChartView />} />
          <Route path="/audit" element={<AuditLogView />} />
          <Route path="/usage" element={<UsageView />} />
          <Route path="/mind/:agentId?" element={<MindView />} />
          <Route path="/memory/:agentId?" element={<MindView />} />
          <Route path="/plugins" element={<PluginBrowser />} />
          <Route path="/plugins/new" element={<PluginCreateView />} />
          <Route path="/skills" element={<SkillBrowser />} />
          <Route path="/skills/new" element={<SkillCreateView />} />
          <Route path="/sandboxes" element={<SandboxImagesView />} />
          <Route path="/repos" element={<GitRepoList />} />
          <Route path="/artifacts" element={<ArtifactViewer />} />
          <Route path="/analytics" element={<AnalyticsView />} />
          <Route path="/docs/:vaultId/*" element={<DocumentView />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
