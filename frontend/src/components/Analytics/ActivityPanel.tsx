import type { ActivityDay } from "../../stores/analyticsStore";

function BarChart({ data }: { data: ActivityDay[] }) {
  if (data.length === 0) return <p className="text-xs text-base-content/40">No activity data yet.</p>;

  const max = Math.max(...data.map((d) => d.actions), 1);
  const barWidth = Math.max(4, Math.min(12, Math.floor(600 / data.length) - 2));

  return (
    <div className="flex items-end gap-px h-28 w-full">
      {data.map((day) => {
        const height = Math.max(2, (day.actions / max) * 100);
        return (
          <div key={day.date} className="group relative flex-1 flex flex-col items-center justify-end">
            <div
              className="w-full rounded-t bg-primary/60 group-hover:bg-primary transition-colors min-w-[3px]"
              style={{ height: `${height}%`, maxWidth: `${barWidth}px` }}
            />
            <div className="absolute bottom-full mb-2 hidden group-hover:block z-10">
              <div className="bg-base-300 border border-base-content/10 rounded px-2 py-1 text-[10px] whitespace-nowrap shadow-lg">
                <div className="font-medium text-base-content">{day.date}</div>
                <div className="text-base-content/60">{day.actions} actions</div>
                <div className="text-base-content/60">{day.unique_agents} agents</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function ActivityPanel({ timeline }: { timeline: ActivityDay[] }) {
  const totalActions = timeline.reduce((s, d) => s + d.actions, 0);
  const avgDaily = timeline.length > 0 ? Math.round(totalActions / timeline.length) : 0;
  const peakDay = timeline.reduce(
    (peak, d) => (d.actions > peak.actions ? d : peak),
    { date: "-", actions: 0, unique_agents: 0 },
  );

  return (
    <div className="card card-border bg-base-300/30">
      <div className="card-body p-5">
        <h2 className="text-base font-semibold text-base-content mb-4">Activity Timeline</h2>

        <div className="flex gap-6 mb-4">
          <div>
            <div className="text-lg font-bold text-base-content tabular-nums">{totalActions}</div>
            <div className="text-[10px] text-base-content/60">Total actions</div>
          </div>
          <div>
            <div className="text-lg font-bold text-base-content tabular-nums">{avgDaily}</div>
            <div className="text-[10px] text-base-content/60">Avg daily</div>
          </div>
          <div>
            <div className="text-lg font-bold text-base-content tabular-nums">{peakDay.actions}</div>
            <div className="text-[10px] text-base-content/60">Peak ({peakDay.date.slice(5)})</div>
          </div>
        </div>

        <BarChart data={timeline} />

        {timeline.length > 0 && (
          <div className="flex justify-between mt-2 text-[10px] text-base-content/40">
            <span>{timeline[0]?.date.slice(5)}</span>
            <span>{timeline[timeline.length - 1]?.date.slice(5)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
