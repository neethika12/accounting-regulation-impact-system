// Production builds (e.g. the Vercel deployment) have no live backend to
// talk to, so they fetch pre-generated static JSON snapshots instead --
// see scripts/export_static_data.py. Local `npm run dev` always talks to
// the live FastAPI backend via the Vite proxy (see vite.config.js).
const STATIC_MODE = import.meta.env.PROD;

const ROUTES = {
  summary: { live: "/api/summary", static: "/data/summary.json" },
  standards: { live: "/api/standards", static: "/data/standards.json" },
  metrics: { live: "/api/metrics", static: "/data/metrics.json" },
};

async function getJson(key) {
  const url = STATIC_MODE ? ROUTES[key].static : ROUTES[key].live;
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  summary: () => getJson("summary"),
  standards: () => getJson("standards"),
  metrics: () => getJson("metrics"),
};
