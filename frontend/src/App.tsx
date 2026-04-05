import { Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { LayoutShell } from "./components/Layout/LayoutShell";
import { TabRedirect } from "./components/Layout/TabRedirect";

export default function App() {
  return (
    <Suspense>
      <Routes>
        <Route element={<LayoutShell />}>
          <Route path="/" element={<TabRedirect />} />
          <Route path="/huddle" element={<TabRedirect />} />
          <Route path="/agent/:agentId" element={<TabRedirect />} />
          <Route path="/dashboard" element={<TabRedirect />} />
          <Route path="/tasks" element={<TabRedirect />} />
          <Route path="/calendar" element={<TabRedirect />} />
          <Route path="/approvals" element={<TabRedirect />} />
          <Route path="/issues" element={<TabRedirect />} />
          <Route path="/achievements" element={<TabRedirect />} />
          <Route path="/org-chart" element={<TabRedirect />} />
          <Route path="/audit" element={<TabRedirect />} />
          <Route path="/usage" element={<TabRedirect />} />
          <Route path="/mind/:agentId?" element={<TabRedirect />} />
          <Route path="/memory/:agentId?" element={<TabRedirect />} />
          <Route path="/plugins" element={<TabRedirect />} />
          <Route path="/plugins/new" element={<TabRedirect />} />
          <Route path="/skills" element={<TabRedirect />} />
          <Route path="/skills/new" element={<TabRedirect />} />
          <Route path="/sandboxes" element={<TabRedirect />} />
          <Route path="/repos" element={<TabRedirect />} />
          <Route path="/artifacts" element={<TabRedirect />} />
          <Route path="/documents" element={<TabRedirect />} />
          <Route path="/analytics" element={<TabRedirect />} />
          <Route path="/docs/:vaultId/*" element={<TabRedirect />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
