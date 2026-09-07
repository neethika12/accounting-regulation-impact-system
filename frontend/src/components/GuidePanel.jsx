import { useState } from "react";

const STORAGE_KEY = "guide-panel-open";

function readInitialOpen() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === null ? true : stored === "true";
  } catch {
    return true;
  }
}

export default function GuidePanel() {
  const [open, setOpen] = useState(readInitialOpen);

  function toggle() {
    const next = !open;
    setOpen(next);
    try {
      localStorage.setItem(STORAGE_KEY, String(next));
    } catch {
      // ignore -- private browsing / storage blocked
    }
  }

  return (
    <div className="rounded-xl border border-violet-200 bg-violet-50 dark:border-violet-900 dark:bg-violet-950/40">
      <button
        onClick={toggle}
        className="flex w-full items-center justify-between px-4 py-3 text-left"
      >
        <span className="text-sm font-semibold text-violet-900 dark:text-violet-200">
          📘 New here? How to read this dashboard
        </span>
        <span className="text-xs font-medium text-violet-700 dark:text-violet-300">
          {open ? "Hide guide" : "Show guide"}
        </span>
      </button>

      {open && (
        <div className="space-y-4 border-t border-violet-200 px-4 py-4 text-sm text-slate-700 dark:border-violet-900 dark:text-slate-300">
          <section>
            <h3 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
              What is this?
            </h3>
            <p>
              FASB is the U.S. board that writes accounting rules companies must
              follow. Whenever FASB issues a new rule, companies have to figure out
              when and how to start following it. This tool tracks 15 real FASB
              rule changes and measures how companies typically respond: how
              quickly they adopt a new rule, how often adopting it leads to a
              correction, and how much extra it costs in audit work.
            </p>
          </section>

          <section>
            <h3 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
              What's real and what's simulated
            </h3>
            <p>
              The 15 rule changes and their real dates are genuine public record
              (things like the 2014 revenue-recognition rule or the 2016 leases
              rule). Real company-by-company data on who adopted what and when
              requires an expensive research subscription this project doesn't
              have — so the company-level numbers below are realistically
              generated examples, used to demonstrate how the analysis works.
              This is explained again at the bottom of the page.
            </p>
          </section>

          <section>
            <h3 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
              What the top numbers mean
            </h3>
            <ul className="ml-4 list-disc space-y-1">
              <li><strong>ASU Standards</strong> — how many real rule changes are tracked.</li>
              <li><strong>Firms Tracked</strong> — how many example companies are simulated.</li>
              <li><strong>Adoption Records</strong> — total company × rule combinations measured.</li>
              <li><strong>Avg Restatement Rate</strong> — how often adopting a rule led to a correction, on average.</li>
              <li><strong>Avg Deliberation Lag</strong> — how many days FASB typically spent finalizing a rule after collecting public feedback, before issuing it.</li>
            </ul>
          </section>

          <section>
            <h3 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
              How to read the charts
            </h3>
            <ul className="ml-4 list-disc space-y-1">
              <li><strong>Timeline</strong> — each bar spans from when a rule was issued to when companies had to start following it.</li>
              <li><strong>Adoption Timing Mix</strong> — for each rule, how many example companies adopted early, on time, or late.</li>
              <li><strong>Deliberation Lag vs. Restatement Rate</strong> — checks whether rules that took longer for FASB to finalize tend to have messier adoption (more corrections).</li>
              <li><strong>Detail table</strong> — every number above, broken out rule by rule.</li>
            </ul>
          </section>

          <section>
            <h3 className="mb-1 font-semibold text-slate-900 dark:text-slate-100">
              Try uploading your own data
            </h3>
            <p>
              Scroll to the <strong>"Try Your Own Data"</strong> section near the
              bottom. Download the template CSV to see the required format, then
              upload any CSV of rule changes — real or made up. Your file runs
              through the same validation and calculations as the real dataset
              above (nothing is saved). If a row is missing required dates or has
              a duplicate ID, you'll see the exact same error the tool would show
              on bad real-world data.
            </p>
          </section>
        </div>
      )}
    </div>
  );
}
