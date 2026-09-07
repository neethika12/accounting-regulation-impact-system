import { useRef, useState } from "react";
import { api } from "../lib/api";
import StandardsTable from "./StandardsTable";

export default function TryYourOwnData() {
  const fileInputRef = useRef(null);
  const [fileName, setFileName] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error | success
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setStatus("loading");
    setError(null);
    setResult(null);

    try {
      const response = await api.uploadStandards(file);
      if (response.valid) {
        setResult(response);
        setStatus("success");
      } else {
        setError(response.error);
        setStatus("error");
      }
    } catch (err) {
      setError(err.message);
      setStatus("error");
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-1 text-sm font-semibold text-slate-900 dark:text-slate-50">
        Try Your Own Data
      </h2>
      <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
        Upload a CSV of standards in the same format as the real dataset above. This
        runs the file through the actual ingestion, validation, and metrics code from
        the pipeline (not a demo simulation) — a malformed file is rejected with the
        pipeline's real error message.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <label className="cursor-pointer rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-violet-700">
          Upload CSV
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>
        <a
          href="/template_standards.csv"
          download
          className="text-xs font-medium text-violet-600 hover:underline dark:text-violet-400"
        >
          Download a template CSV
        </a>
        {fileName && (
          <span className="text-xs text-slate-500 dark:text-slate-400">{fileName}</span>
        )}
      </div>

      {status === "loading" && (
        <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">Processing…</p>
      )}

      {status === "error" && (
        <div className="mt-3 rounded-lg border border-red-300 bg-red-50 p-3 text-xs text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
          <p className="font-semibold">Rejected by the pipeline's validation:</p>
          <p className="mt-1 font-mono">{error}</p>
        </div>
      )}

      {status === "success" && result && (
        <div className="mt-4">
          <div className="mb-3 rounded-lg border border-emerald-300 bg-emerald-50 p-3 text-xs text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            Validated and processed {result.n_standards} standard
            {result.n_standards === 1 ? "" : "s"} — metrics below are computed fresh
            from your file, nothing is saved.
          </div>
          <StandardsTable metrics={result.metrics} />
        </div>
      )}
    </div>
  );
}
