import AdoptionMixChart from "./components/AdoptionMixChart";
import RestatementScatter from "./components/RestatementScatter";
import StandardsTable from "./components/StandardsTable";
import StandardsTimeline from "./components/StandardsTimeline";
import SummaryCards from "./components/SummaryCards";
import { api } from "./lib/api";
import { useApiData } from "./lib/useApiData";

function ErrorBanner({ error }) {
  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200">
      <p className="font-semibold">Couldn't reach the API.</p>
      <p className="mt-1">{error.message}</p>
      <p className="mt-2 text-xs">
        Make sure the backend is running:{" "}
        <code className="rounded bg-amber-100 px-1 py-0.5 dark:bg-amber-900">
          uvicorn src.api:app --reload --port 8000
        </code>{" "}
        and that the pipeline has been run at least once:{" "}
        <code className="rounded bg-amber-100 px-1 py-0.5 dark:bg-amber-900">python -m src.pipeline</code>
      </p>
    </div>
  );
}

export default function App() {
  const { data: summary, error: summaryError } = useApiData(api.summary);
  const { data: standards, error: standardsError } = useApiData(api.standards);
  const { data: metrics, error: metricsError } = useApiData(api.metrics);

  const error = summaryError || standardsError || metricsError;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">
            Accounting Regulation Analysis &amp; Standard-Setting Impact Measurement
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            15 real FASB Accounting Standards Updates, tracked against a synthetic
            firm-adoption panel used to demonstrate the impact-measurement methodology.
          </p>
        </header>

        {error ? (
          <ErrorBanner error={error} />
        ) : (
          <div className="flex flex-col gap-5">
            <SummaryCards summary={summary} />
            <StandardsTimeline standards={standards} />
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <AdoptionMixChart metrics={metrics} />
              <RestatementScatter metrics={metrics} />
            </div>
            <StandardsTable metrics={metrics} />
            <footer className="pb-4 text-center text-xs text-slate-400 dark:text-slate-600">
              Standards metadata is real (public FASB record). Firm-level adoption
              timing, restatements, and audit fees are synthetic (seeded, reproducible)
              — see docs/DATA_SOURCES.md.
            </footer>
          </div>
        )}
      </div>
    </div>
  );
}
