import { useEffect, useState } from "react";
import { useSettingsStore } from "../../stores/settingsStore";
import { useNotifications } from "../../hooks/useNotifications";

function getTheme(): "axon" | "axon-dark" {
  const stored = localStorage.getItem("axon-theme");
  if (stored === "axon" || stored === "axon-dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "axon-dark"
    : "axon";
}

export function GeneralTab() {
  const [theme, setTheme] = useState(getTheme);
  const { savePreferences, preferences } = useSettingsStore();

  // Sync from API on first load (if API returned a theme)
  useEffect(() => {
    if (preferences?.theme) {
      const apiTheme = preferences.theme === "dark" ? "axon-dark" : "axon";
      if (apiTheme !== theme) setTheme(apiTheme);
    }
  }, [preferences?.theme]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("axon-theme", theme);
  }, [theme]);

  const toggle = () => {
    const next = theme === "axon" ? "axon-dark" : "axon";
    setTheme(next);
    // Persist to API (fire-and-forget)
    savePreferences({ theme: next === "axon-dark" ? "dark" : "light" });
  };

  const notifications = useNotifications();

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-sm font-semibold mb-3">Appearance</h4>
        <label className="flex items-center justify-between gap-3 cursor-pointer">
          <div>
            <span className="text-sm">Dark mode</span>
            <p className="text-xs text-base-content/60 mt-0.5">
              Switch between light and dark theme
            </p>
          </div>
          <input
            type="checkbox"
            className="toggle toggle-sm toggle-primary"
            checked={theme === "axon-dark"}
            onChange={toggle}
          />
        </label>
      </div>

      <div>
        <h4 className="text-sm font-semibold mb-3">Notifications</h4>
        {!notifications.supported ? (
          <p className="text-xs text-base-content/50">
            Push notifications are not supported in this browser.
          </p>
        ) : notifications.permission === "denied" ? (
          <p className="text-xs text-base-content/50">
            Notifications are blocked. Enable them in your browser settings for
            this site, then reload.
          </p>
        ) : (
          <label className="flex items-center justify-between gap-3 cursor-pointer">
            <div>
              <span className="text-sm">Push notifications</span>
              <p className="text-xs text-base-content/60 mt-0.5">
                Get notified when agents complete tasks, even when Axon isn't
                open
              </p>
            </div>
            <input
              type="checkbox"
              className="toggle toggle-sm toggle-primary"
              checked={notifications.enabled}
              disabled={notifications.loading}
              onChange={(e) =>
                e.target.checked
                  ? notifications.enable()
                  : notifications.disable()
              }
            />
          </label>
        )}
      </div>
    </div>
  );
}
