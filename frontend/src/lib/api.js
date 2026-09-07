const BASE = "/api";

async function getJson(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  health: () => getJson("/health"),
  summary: () => getJson("/summary"),
  standards: () => getJson("/standards"),
  metrics: () => getJson("/metrics"),
  firmAdoptions: (asuNumber) =>
    getJson(asuNumber ? `/firm-adoptions?asu_number=${encodeURIComponent(asuNumber)}` : "/firm-adoptions"),
  benchmarks: () => getJson("/benchmarks"),
};
