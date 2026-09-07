import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function AdoptionMixChart({ metrics }) {
  if (!metrics?.length) return null;

  const rows = [...metrics]
    .sort((a, b) => (a.issued_date < b.issued_date ? -1 : 1))
    .map((m) => ({
      asu_number: m.asu_number,
      Early: m.n_early_adopters,
      "On-time": m.n_on_time_adopters,
      Late: m.n_late_adopters,
    }));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-1 text-sm font-semibold text-slate-900 dark:text-slate-50">
        Adoption Timing Mix
      </h2>
      <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
        Firms adopting early / within 90 days / late, per standard (synthetic panel)
      </p>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={rows} margin={{ left: -12, right: 8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" opacity={0.15} />
          <XAxis dataKey="asu_number" stroke="currentColor" opacity={0.6} fontSize={11} angle={-40} textAnchor="end" height={60} />
          <YAxis stroke="currentColor" opacity={0.6} fontSize={12} />
          <Tooltip
            contentStyle={{ fontSize: 12 }}
            wrapperClassName="!rounded-lg !border-slate-200 dark:!border-slate-700"
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="Early" stackId="mix" fill="#38bdf8" isAnimationActive={false} />
          <Bar dataKey="On-time" stackId="mix" fill="#34d399" isAnimationActive={false} />
          <Bar dataKey="Late" stackId="mix" fill="#f87171" radius={[3, 3, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
