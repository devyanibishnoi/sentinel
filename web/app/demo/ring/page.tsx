import Link from "next/link";
import ringsData from "@/data/rings.json";
import demoRingsData from "@/data/demo_rings.json";
import { RingCluster } from "@/lib/types";
import { SourceBadge } from "@/components/Badge";
import { Caveat } from "@/components/Caveat";

const clusters: (RingCluster & { source: "benchmark" | "demo" })[] = [
  ...(ringsData.clusters as RingCluster[]).map((c) => ({ ...c, source: "benchmark" as const })),
  ...(demoRingsData.clusters as RingCluster[]).map((c) => ({ ...c, source: "demo" as const })),
].sort((a, b) => (b.proxy_fraud_rate ?? b.avg_population_score ?? 0) - (a.proxy_fraud_rate ?? a.avg_population_score ?? 0));

export default function RingListPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="text-2xl font-semibold mb-1">Ring Viewer</h1>
      <p className="text-text-muted text-sm mb-5">
        Each row is a group of accounts that share a device fingerprint, how that&apos;s detected is explained on{" "}
        <Link href="/#how-it-works" className="text-accent hover:underline">
          the case study
        </Link>
        .
      </p>
      <Caveat tone="warning">
        <strong className="text-text">Benchmark</strong> clusters: fraud rate is a <strong className="text-text">derived proxy</strong>,
        not verified ground truth, shown only if size (5+ transactions) and fraud rate (≥3x baseline) both passed.{" "}
        <strong className="text-text">Demo</strong> clusters have no ground truth at all, credibility there comes from
        structure plus a corroborating score, not a fraud rate.
      </Caveat>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-text-muted border-b border-border">
              <th className="px-3 py-2.5 font-medium">Cluster</th>
              <th className="px-3 py-2.5 font-medium">Source</th>
              <th className="px-3 py-2.5 font-medium">Accounts</th>
              <th className="px-3 py-2.5 font-medium">Transactions</th>
              <th className="px-3 py-2.5 font-medium">Signal</th>
            </tr>
          </thead>
          <tbody>
            {clusters.map((c) => (
              <tr key={c.cluster_id} className="border-b border-border last:border-0 hover:bg-surface-raised transition-colors">
                <td className="px-3 py-2.5">
                  <Link href={`/demo/ring/${c.cluster_id}`} className="text-accent hover:underline">
                    {c.cluster_id}
                  </Link>
                </td>
                <td className="px-3 py-2.5">
                  <SourceBadge source={c.source} />
                </td>
                <td className="px-3 py-2.5 tabular-nums">{c.n_entities}</td>
                <td className="px-3 py-2.5 tabular-nums">{c.n_transactions}</td>
                <td className="px-3 py-2.5 font-mono text-xs">
                  {c.proxy_fraud_rate !== null
                    ? `${(c.proxy_fraud_rate * 100).toFixed(1)}% proxy fraud rate`
                    : `avg. population score ${c.avg_population_score?.toFixed(3)}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
