import { lazy, type ComponentType } from "react";
import type { TabType } from "../../stores/tabStore";

interface TabTypeConfig {
  label: string;
  component: ComponentType<any>;
  /** Derive route path from tab params for URL sync */
  toPath?: (agentId?: string, params?: Record<string, string>) => string;
}

const AgentView = lazy(() => import("../Conversation/AgentView").then(m => ({ default: m.AgentView })));
const AxonView = lazy(() => import("../AxonView/AxonView").then(m => ({ default: m.AxonView })));
const DashboardView = lazy(() => import("../Dashboard/DashboardView").then(m => ({ default: m.DashboardView })));
const HuddleView = lazy(() => import("../Huddle/HuddleView").then(m => ({ default: m.HuddleView })));
const TaskBoardView = lazy(() => import("../Tasks/TaskBoardView").then(m => ({ default: m.TaskBoardView })));
const CalendarView = lazy(() => import("../Calendar/CalendarView").then(m => ({ default: m.CalendarView })));
const ApprovalsView = lazy(() => import("../Approvals/ApprovalsView").then(m => ({ default: m.ApprovalsView })));
const IssueListView = lazy(() => import("../Issues/IssueListView").then(m => ({ default: m.IssueListView })));
const AnalyticsView = lazy(() => import("../Analytics/AnalyticsView").then(m => ({ default: m.AnalyticsView })));
const AchievementsView = lazy(() => import("../Achievements/AchievementsView").then(m => ({ default: m.AchievementsView })));
const MindView = lazy(() => import("../Mind/MindView").then(m => ({ default: m.MindView })));
const OrgChartView = lazy(() => import("../OrgChart/OrgChartView").then(m => ({ default: m.OrgChartView })));
const AuditLogView = lazy(() => import("../AuditLog/AuditLogView").then(m => ({ default: m.AuditLogView })));
const UsageView = lazy(() => import("../Usage/UsageView").then(m => ({ default: m.UsageView })));
const PluginBrowser = lazy(() => import("../Plugins/PluginBrowser").then(m => ({ default: m.PluginBrowser })));
const PluginCreateView = lazy(() => import("../Plugins/PluginCreateView").then(m => ({ default: m.PluginCreateView })));
const SkillBrowser = lazy(() => import("../Skills/SkillBrowser").then(m => ({ default: m.SkillBrowser })));
const SkillCreateView = lazy(() => import("../Skills/SkillCreateView").then(m => ({ default: m.SkillCreateView })));
const SandboxImagesView = lazy(() => import("../Sandbox/SandboxImagesView").then(m => ({ default: m.SandboxImagesView })));
const ArtifactViewer = lazy(() => import("../Artifacts/ArtifactViewer").then(m => ({ default: m.ArtifactViewer })));
const GitRepoList = lazy(() => import("../GitRepos/GitRepoList").then(m => ({ default: m.GitRepoList })));
const DocumentLibrary = lazy(() => import("../Documents/DocumentLibrary").then(m => ({ default: m.DocumentLibrary })));
const DocumentView = lazy(() => import("../Documents/DocumentView").then(m => ({ default: m.DocumentView })));

export const TAB_REGISTRY: Record<TabType, TabTypeConfig> = {
  axon:           { label: "Axon",          component: AxonView,          toPath: () => "/" },
  chat:           { label: "Chat",          component: AgentView,         toPath: (id) => `/agent/${id}` },
  dashboard:      { label: "Dashboard",     component: DashboardView,     toPath: () => "/dashboard" },
  huddle:         { label: "Huddle",        component: HuddleView,        toPath: () => "/huddle" },
  tasks:          { label: "Tasks",         component: TaskBoardView,     toPath: () => "/tasks" },
  calendar:       { label: "Calendar",      component: CalendarView,      toPath: () => "/calendar" },
  approvals:      { label: "Approvals",     component: ApprovalsView,     toPath: () => "/approvals" },
  issues:         { label: "Issues",        component: IssueListView,     toPath: () => "/issues" },
  analytics:      { label: "Analytics",     component: AnalyticsView,     toPath: () => "/analytics" },
  achievements:   { label: "Achievements",  component: AchievementsView,  toPath: () => "/achievements" },
  memory:         { label: "Mind",          component: MindView,          toPath: (id) => id ? `/mind/${id}` : "/mind" },
  "org-chart":    { label: "Org Chart",     component: OrgChartView,      toPath: () => "/org-chart" },
  audit:          { label: "Audit Log",     component: AuditLogView,      toPath: () => "/audit" },
  usage:          { label: "Usage",         component: UsageView,         toPath: () => "/usage" },
  plugins:        { label: "Plugins",       component: PluginBrowser,     toPath: () => "/plugins" },
  "plugin-create":{ label: "New Plugin",    component: PluginCreateView,  toPath: () => "/plugins/new" },
  skills:         { label: "Skills",        component: SkillBrowser,      toPath: () => "/skills" },
  "skill-create": { label: "New Skill",     component: SkillCreateView,   toPath: () => "/skills/new" },
  sandboxes:      { label: "Sandboxes",     component: SandboxImagesView, toPath: () => "/sandboxes" },
  artifacts:      { label: "Artifacts",     component: ArtifactViewer,    toPath: () => "/artifacts" },
  repos:          { label: "Repos",         component: GitRepoList,       toPath: () => "/repos" },
  documents:      { label: "Documents",     component: DocumentLibrary,   toPath: () => "/documents" },
  document:       { label: "Document",      component: DocumentView,      toPath: (_, p) => `/docs/${p?.vaultId}/${p?.path || ""}` },
  welcome:        { label: "Welcome",       component: DashboardView,     toPath: () => "/dashboard" },
};

/** Map route paths back to tab types for URL → tab sync */
export const ROUTE_TO_TAB: { pattern: RegExp; type: TabType; extract?: (match: RegExpMatchArray) => Partial<{ agentId: string; label: string; params: Record<string, string> }> }[] = [
  { pattern: /^\/$/,                  type: "axon" },
  { pattern: /^\/dashboard$/,         type: "dashboard" },
  { pattern: /^\/huddle$/,            type: "huddle" },
  { pattern: /^\/agent\/([^/]+)$/,    type: "chat",          extract: (m) => ({ agentId: m[1], label: m[1] }) },
  { pattern: /^\/tasks$/,             type: "tasks" },
  { pattern: /^\/calendar$/,          type: "calendar" },
  { pattern: /^\/approvals$/,         type: "approvals" },
  { pattern: /^\/issues$/,            type: "issues" },
  { pattern: /^\/analytics$/,         type: "analytics" },
  { pattern: /^\/achievements$/,      type: "achievements" },
  { pattern: /^\/mind(?:\/([^/]+))?$/,type: "memory",        extract: (m) => m[1] ? { agentId: m[1] } : {} },
  { pattern: /^\/memory(?:\/([^/]+))?$/,type: "memory",      extract: (m) => m[1] ? { agentId: m[1] } : {} },
  { pattern: /^\/documents$/,         type: "documents" },
  { pattern: /^\/org-chart$/,         type: "org-chart" },
  { pattern: /^\/audit$/,             type: "audit" },
  { pattern: /^\/usage$/,             type: "usage" },
  { pattern: /^\/plugins\/new$/,      type: "plugin-create" },
  { pattern: /^\/plugins$/,           type: "plugins" },
  { pattern: /^\/skills\/new$/,       type: "skill-create" },
  { pattern: /^\/skills$/,            type: "skills" },
  { pattern: /^\/sandboxes$/,         type: "sandboxes" },
  { pattern: /^\/repos$/,             type: "repos" },
  { pattern: /^\/artifacts$/,         type: "artifacts" },
  { pattern: /^\/docs\/([^/]+)\/(.*)$/, type: "document",    extract: (m) => ({ params: { vaultId: m[1], path: m[2] } }) },
];
