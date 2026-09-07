# Deployment (Vercel)

The dashboard deploys to Vercel as a **fully static site** — no live backend
is hosted there. Production builds fetch pre-generated JSON snapshots
(`frontend/public/data/*.json`) instead of calling the FastAPI backend;
`frontend/src/lib/api.js` switches automatically based on `import.meta.env.PROD`
(true for any production build, false for `npm run dev`).

This is a deliberate choice, not a limitation worked around: the underlying
data is deterministic (seeded synthetic panel + static real FASB records), so
there is nothing a live backend would compute differently at request time.
Serving static JSON is simpler, has zero cold-start latency, and needs no
server hosting/billing for what is a demo/portfolio deployment.

## Regenerating the snapshot

Whenever `data/seed_asu_standards.csv` or the metrics logic in `src/` changes:

```bash
python -m src.pipeline
python scripts/export_static_data.py
git add frontend/public/data/*.json
git commit -m "Regenerate static dashboard snapshot"
git push
```

Vercel redeploys automatically on push (if the GitHub integration is connected).

## Importing into Vercel

1. Go to https://vercel.com/new and sign in (GitHub login recommended, since
   this repo is already on GitHub).
2. Click **Import Project**, select
   `neethika12/accounting-regulation-impact-system`.
3. Vercel auto-detects the root-level `vercel.json`, which points the build
   at `frontend/` and its output at `frontend/dist` — no manual framework or
   root-directory configuration should be needed.
4. Click **Deploy**. First build takes ~1 minute.
5. Vercel gives you a `https://<project>.vercel.app` URL — that's the
   shareable link.

## Running the live (non-static) version locally

The Vercel deployment intentionally has no backend. To run the full stack
with the live FastAPI backend and R analysis, see the main
[README.md](../README.md) Quickstart instead.
