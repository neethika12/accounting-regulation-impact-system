import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const DAY_MS = 86_400_000;

function daysBetween(a, b) {
  return Math.round((new Date(b).getTime() - new Date(a).getTime()) / DAY_MS);
}

export default function StandardsTimeline({ standards }) {
  if (!standards?.length) return null;

  const minDate = standards.reduce(
    (min, s) => (s.issued_date < min ? s.issued_date : min),
    standards[0].issued_date
  );

  const rows = standards
    .map((s) => ({
      asu_number: s.asu_number,
      title: s.title,
      topic_code: s.topic_code,
      offset: daysBetween(minDate, s.issued_date),
      duration: daysBetween(s.issued_date, s.effective_date_public),
      issued_date: s.issued_date,
      effective_date_public: s.effective_date_public,
    }))
    .sort((a, b) => a.offset - b.offset);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-1 text-sm font-semibold text-slate-900 dark:text-slate-50">
        Standard-Setting Timeline
      </h2>
      <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
        Issuance → public-entity effective date, per ASU
      </p>
      <ResponsiveContainer width="100%" height={Math.max(320, rows.length * 34)}>
        <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="currentColor" opacity={0.15} />
          <XAxis
            type="number"
            tickFormatter={(v) => `${Math.round(v / 365)}y`}
            stroke="currentColor"
            opacity={0.6}
            fontSize={12}
          />
          <YAxis
            type="category"
            dataKey="asu_number"
            width={70}
            stroke="currentColor"
            opacity={0.6}
            fontSize={12}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const row = payload[0].payload;
              return (
                <div className="rounded-lg border border-slate-200 bg-white p-2 text-xs shadow-lg dark:border-slate-700 dark:bg-slate-800">
                  <div className="font-semibold">
                    ASU {row.asu_number} — Topic {row.topic_code}
                  </div>
                  <div className="text-slate-500 dark:text-slate-400">{row.title}</div>
                  <div className="mt-1">Issued: {row.issued_date}</div>
                  <div>Effective: {row.effective_date_public}</div>
                </div>
              );
            }}
          />
          <Bar dataKey="offset" stackId="a" fill="transparent" isAnimationActive={false} />
          <Bar dataKey="duration" stackId="a" radius={[3, 3, 3, 3]} isAnimationActive={false}>
            {rows.map((r) => (
              <Cell key={r.asu_number} fill="#7c3aed" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
