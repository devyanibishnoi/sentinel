import comparisonData from "@/data/comparison.json";
import baselinesData from "@/data/baselines.json";
import { BaselineRow, ComparisonRow } from "@/lib/types";
import { Caveat } from "@/components/Caveat";
import { StatTile } from "@/components/StatTile";
import { BarChart } from "@/components/BarChart";

const comparison = [...(comparisonData.results as ComparisonRow[])].sort(
  (a, b) => b.pr_auc_full_test - a.pr_auc_full_test
);
const baselines = baselinesData as BaselineRow[];
const diag = comparisonData.history_depth_diagnostic;

const chartData = comparison.map((r, i) => ({
  label: r.method
    .replace("isolation_forest (population-only)", "IsolationForest, population-only")
    .replace("isolation_forest (population + entity-deviation)", "IsolationForest, +entity-deviation")
    .replace(/\s*\(.*\)/, ""),
  value: r.pr_auc_full_test,
  emphasis: i === 0,
}));

export default function MetricsPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="text-2xl font-semibold mb-1">Metrics</h1>
      <p className="text-text-muted text-sm mb-5">
        Start here if you&apos;re only checking one page, every number quoted elsewhere on this site traces back to
        this one. All of it comes from the held-out BENCHMARK test split only, 85,004 transactions. The demo stream
        never contributes to a reported metric.
      </p>

      <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted mt-8 mb-3">
        Detector vs. all four required baselines (PR-AUC)
      </h2>
      <div className="rounded-lg border border-border bg-surface p-6 mb-3">
        <BarChart data={chartData} />
      </div>
      <details className="mb-8 text-xs text-text-muted">
        <summary className="cursor-pointer hover:text-text transition-colors w-fit">
          Also show PR-AUC restricted to has-history rows only
        </summary>
        <div className="overflow-x-auto rounded-lg border border-border mt-3">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-text-muted border-b border-border">
                <th className="px-3 py-2 font-medium">Method</th>
                <th className="px-3 py-2 font-medium">PR-AUC (full test)</th>
                <th className="px-3 py-2 font-medium">PR-AUC (has-history only)</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((r) => (
                <tr key={r.method} className="border-b border-border last:border-0">
                  <td className="px-3 py-2">{r.method}</td>
                  <td className="px-3 py-2 font-mono tabular-nums">{r.pr_auc_full_test.toFixed(4)}</td>
                  <td className="px-3 py-2 font-mono tabular-nums text-text-muted">
                    {r.pr_auc_has_history_only.toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted mt-8 mb-3">
        The entity-vs-population lift, and why it&apos;s not positive
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
        <StatTile value={`${(comparisonData.has_history_share * 100).toFixed(1)}%`} label="test rows with any entity history" />
        <StatTile value={`${diag.median_prior_count_among_has_history}`} label="median prior transactions (has-history rows)" />
        <StatTile value={`${(diag.exactly_one_prior_share_of_has_history * 100).toFixed(1)}%`} label="has-history rows with only 1 prior" />
      </div>
      <p className="text-sm text-text-muted mb-8 max-w-3xl">
        Entity-deviation does not improve PR-AUC over population-only, confirmed even restricted to has-history rows.
        Root cause: most account histories in this slice of data are too thin to baseline against. Full
        investigation in the project&apos;s Learning Log, decision recorded as ADR-0007.
      </p>

      <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted mt-8 mb-3">
        Day 1 baselines, population and entity level
      </h2>
      <Caveat>
        These exist to be beaten, not to be good. The random baseline landing almost exactly on the true fraud rate
        is the actual sanity check that the pipeline is wired correctly.
      </Caveat>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-text-muted border-b border-border">
              <th className="px-3 py-2.5 font-medium">Baseline</th>
              <th className="px-3 py-2.5 font-medium">Precision</th>
              <th className="px-3 py-2.5 font-medium">Recall</th>
              <th className="px-3 py-2.5 font-medium">FPR</th>
            </tr>
          </thead>
          <tbody>
            {baselines.map((b) => (
              <tr key={b.baseline} className="border-b border-border last:border-0">
                <td className="px-3 py-2.5">{b.baseline}</td>
                <td className="px-3 py-2.5 font-mono tabular-nums">{b.precision.toFixed(4)}</td>
                <td className="px-3 py-2.5 font-mono tabular-nums">{b.recall.toFixed(4)}</td>
                <td className="px-3 py-2.5 font-mono tabular-nums">{b.fpr.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
