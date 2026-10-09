import { RingCluster } from "@/lib/types";

export function RingGraph({ cluster }: { cluster: RingCluster }) {
  const devices = Array.from(new Set(cluster.edges.map((e) => e.DeviceInfo))).sort();
  const nodeIds = [...cluster.entities, ...devices];
  const cx = 260;
  const cy = 260;
  const r = 210;

  const positions = new Map<string, [number, number]>();
  nodeIds.forEach((id, i) => {
    const angle = (2 * Math.PI * i) / nodeIds.length;
    positions.set(id, [cx + r * Math.cos(angle), cy + r * Math.sin(angle)]);
  });

  return (
    <svg
      width="100%"
      height="520"
      viewBox="0 0 520 520"
      className="rounded-lg border border-border bg-surface"
    >
      {cluster.edges.map((e, i) => {
        const [x1, y1] = positions.get(e.entity_id)!;
        const [x2, y2] = positions.get(e.DeviceInfo)!;
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--border-strong)" strokeWidth={1.5} />;
      })}
      {nodeIds.map((id) => {
        const [x, y] = positions.get(id)!;
        const isEntity = cluster.entities.includes(id);
        return (
          <circle
            key={id}
            cx={x}
            cy={y}
            r={isEntity ? 8 : 10}
            fill={isEntity ? "var(--text-muted)" : "var(--accent)"}
          />
        );
      })}
    </svg>
  );
}
