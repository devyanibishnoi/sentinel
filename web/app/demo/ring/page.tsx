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
      <h1 className="text-2xl font-semibold mb-5">Ring Viewer</h1>
      <Caveat>
        <strong>Benchmark</strong> clusters: proxy fraud rate is a <strong>derived proxy label</strong>, not verified
        ground truth, and only appears here if size (5+ transactions) AND fraud rate (≥3x baseline) both passed.{" "}
        <strong>Demo</strong> clusters have no ground truth at all, credibility there is judged by structure plus a
        corroborating population score, not a fraud rate.
      </Caveat>
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-text-muted border-b border-border">
              <th className="px-3 py-2 font-medium">Cluster</th>
              <th className="px-3 py-2 font-medium">Source</th>
              <th className="px-3 py-2 font-medium">Entities</th>
              <th className="px-3 py-2 font-medium">Transactions</th>
              <th className="px-3 py-2 font-medium">Signal</th>
            </tr>
          </thead>
          <tbody>
            {clusters.map((c) => (
              <tr key={c.cluster_id} className="border-b border-border last:border-0 hover:bg-surface-raised transition-colors">
                <td className="px-3 py-2">
                  <Link href={`/demo/ring/${c.cluster_id}`} className="text-accent hover:underline">
                    {c.cluster_id}
                  </Link>
                </td>
                <td className="px-3 py-2">
                  <SourceBadge source={c.source} />
                </td>
                <td className="px-3 py-2">{c.n_entities}</td>
                <td className="px-3 py-2">{c.n_transactions}</td>
                <td className="px-3 py-2 font-mono text-xs">
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
