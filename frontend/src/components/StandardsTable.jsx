export default function StandardsTable({ metrics }) {
  if (!metrics?.length) return null;

  const fmtPct = (v) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
  const fmtUsd = (v) =>
    v == null ? "—" : `$${Math.round(v).toLocaleString()}`;

  const rows = [...metrics].sort((a, b) => (a.issued_date < b.issued_date ? -1 : 1));

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-50">
        Standard-by-Standard Detail
      </h2>
      <table className="w-full min-w-[820px] border-collapse text-left text-xs">
        <thead>
          <tr className="border-b border-slate-200 text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <th className="py-2 pr-3 font-medium">ASU</th>
            <th className="py-2 pr-3 font-medium">Title</th>
            <th className="py-2 pr-3 font-medium">Topic</th>
            <th className="py-2 pr-3 text-right font-medium">Deliberation Lag</th>
            <th className="py-2 pr-3 text-right font-medium">Issuance → Effective</th>
            <th className="py-2 pr-3 text-right font-medium">Early / On-time / Late</th>
            <th className="py-2 pr-3 text-right font-medium">Restatement Rate</th>
            <th className="py-2 pr-3 text-right font-medium">Avg Audit Fee</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((m) => (
            <tr
              key={m.asu_number}
              className="border-b border-slate-100 text-slate-700 last:border-0 dark:border-slate-800 dark:text-slate-300"
            >
              <td className="py-2 pr-3 font-mono">{m.asu_number}</td>
              <td className="py-2 pr-3">{m.title}</td>
              <td className="py-2 pr-3">{m.topic_code}</td>
              <td className="py-2 pr-3 text-right">{m.deliberation_lag_days} d</td>
              <td className="py-2 pr-3 text-right">{m.issuance_to_effective_days} d</td>
              <td className="py-2 pr-3 text-right">
                {m.n_early_adopters} / {m.n_on_time_adopters} / {m.n_late_adopters}
              </td>
              <td className="py-2 pr-3 text-right">{fmtPct(m.restatement_rate)}</td>
              <td className="py-2 pr-3 text-right">{fmtUsd(m.avg_audit_fee_usd)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
