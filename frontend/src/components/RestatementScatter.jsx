import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";

export default function RestatementScatter({ metrics }) {
  if (!metrics?.length) return null;

  const rows = metrics.map((m) => ({
    asu_number: m.asu_number,
    deliberation_lag_days: m.deliberation_lag_days,
    restatement_rate: m.restatement_rate * 100,
    n_firms_tracked: m.n_firms_tracked,
  }));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-1 text-sm font-semibold text-slate-900 dark:text-slate-50">
        Deliberation Lag vs. Restatement Rate
      </h2>
      <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
        Each point is one ASU standard — does slower FASB deliberation correlate with messier adoption?
      </p>
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart margin={{ left: -12, right: 16, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.15} />
          <XAxis
            type="number"
            dataKey="deliberation_lag_days"
            name="Deliberation lag"
            unit=" days"
            stroke="currentColor"
            opacity={0.6}
            fontSize={12}
          />
          <YAxis
            type="number"
            dataKey="restatement_rate"
            name="Restatement rate"
            unit="%"
            stroke="currentColor"
            opacity={0.6}
            fontSize={12}
          />
          <ZAxis type="number" dataKey="n_firms_tracked" range={[60, 200]} name="Firms tracked" />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const row = payload[0].payload;
              return (
                <div className="rounded-lg border border-slate-200 bg-white p-2 text-xs shadow-lg dark:border-slate-700 dark:bg-slate-800">
                  <div className="font-semibold">ASU {row.asu_number}</div>
                  <div>Deliberation lag: {row.deliberation_lag_days} days</div>
                  <div>Restatement rate: {row.restatement_rate.toFixed(1)}%</div>
                </div>
              );
            }}
          />
          <Scatter data={rows} fill="#f59e0b" isAnimationActive={false} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
