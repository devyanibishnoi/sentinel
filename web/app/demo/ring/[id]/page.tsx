import Link from "next/link";
import { notFound } from "next/navigation";
import ringsData from "@/data/rings.json";
import demoRingsData from "@/data/demo_rings.json";
import { RingCluster, Source } from "@/lib/types";
import { SourceBadge } from "@/components/Badge";
import { Caveat } from "@/components/Caveat";
import { RingGraph } from "@/components/RingGraph";

const allClusters: (RingCluster & { source: Source })[] = [
  ...(ringsData.clusters as RingCluster[]).map((c) => ({ ...c, source: "benchmark" as const })),
  ...(demoRingsData.clusters as RingCluster[]).map((c) => ({ ...c, source: "demo" as const })),
];

export function generateStaticParams() {
  return allClusters.map((c) => ({ id: c.cluster_id }));
}

export default async function RingDetailPage({ params }: PageProps<"/demo/ring/[id]">) {
  const { id } = await params;
  const cluster = allClusters.find((c) => c.cluster_id === id);
  if (!cluster) notFound();

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <h1 className="text-2xl font-semibold mb-5 flex items-center gap-3">
        Ring: {cluster.cluster_id}
        <SourceBadge source={cluster.source} />
      </h1>
      {cluster.proxy_fraud_rate !== null ? (
        <Caveat tone="warning">
          Fraud rate is a <strong className="text-text">derived proxy</strong>, not verified ground truth.{" "}
          {cluster.n_entities} accounts, {cluster.n_transactions} transactions,{" "}
          <strong className="text-text">{(cluster.proxy_fraud_rate * 100).toFixed(1)}%</strong> proxy fraud rate
          (baseline ≈ 4.6%).
        </Caveat>
      ) : (
        <Caveat tone="warning">
          <strong className="text-text">Demo</strong> cluster: no ground truth exists for synthetic data.{" "}
          {cluster.n_entities} accounts, {cluster.n_transactions} transactions, flagged purely by structure (shared
          device, bounded cluster size), average population score{" "}
          <strong className="text-text">{cluster.avg_population_score?.toFixed(3)}</strong> shown as corroborating
          context only, not a filter.
        </Caveat>
      )}
      <RingGraph cluster={cluster} />
      <div className="flex items-center gap-5 text-xs text-text-muted mt-3">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-text-muted" />
          account ({cluster.n_entities})
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-accent" />
          shared device (1)
        </span>
      </div>
      <p className="text-text-faint text-xs mt-2 max-w-md">
        Every line is one account that transacted from the single device at the center. That many unrelated-looking
        accounts converging on one device is the signal, not any individual transaction.
      </p>
      <Link href="/demo/ring" className="text-accent hover:underline text-sm mt-5 inline-block">
        ← back to all rings
      </Link>
    </div>
  );
}
