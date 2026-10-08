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
        <Caveat>
          Proxy fraud rate is a <strong>derived proxy label</strong>, not verified ground truth. {cluster.n_entities}{" "}
          entities, {cluster.n_transactions} transactions,{" "}
          <strong>{(cluster.proxy_fraud_rate * 100).toFixed(1)}%</strong> proxy fraud rate (baseline ≈ 4.6%).
        </Caveat>
      ) : (
        <Caveat>
          <strong>Demo</strong> cluster: no ground truth exists for synthetic data. {cluster.n_entities} entities,{" "}
          {cluster.n_transactions} transactions, flagged purely by structure (shared device, bounded cluster size),
          average population score <strong>{cluster.avg_population_score?.toFixed(3)}</strong> shown as corroborating
          context only, not a filter.
        </Caveat>
      )}
      <RingGraph cluster={cluster} />
      <p className="text-text-muted text-xs mt-3">
        <span className="text-red">●</span> entity &nbsp;&nbsp; <span className="text-blue">●</span> shared device
      </p>
      <Link href="/demo/ring" className="text-accent hover:underline text-sm mt-4 inline-block">
        ← back to all rings
      </Link>
    </div>
  );
}
