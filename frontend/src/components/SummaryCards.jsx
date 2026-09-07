function Card({ label, value, sub }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-50">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{sub}</div>}
    </div>
  );
}

export default function SummaryCards({ summary }) {
  if (!summary) return null;
  const pct = (v) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
  const days = (v) => (v == null ? "—" : `${Math.round(v)} days`);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      <Card label="ASU Standards" value={summary.n_standards} sub="Real FASB standards tracked" />
      <Card label="Firms Tracked" value={summary.n_firms} sub="Synthetic adoption panel" />
      <Card label="Adoption Records" value={summary.n_adoptions} sub="Firm × standard pairs" />
      <Card
        label="Avg Restatement Rate"
        value={pct(summary.avg_restatement_rate)}
        sub="Across all standards"
      />
      <Card
        label="Avg Deliberation Lag"
        value={days(summary.avg_deliberation_lag_days)}
        sub="Comment close → issuance"
      />
    </div>
  );
}
