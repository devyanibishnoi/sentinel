import Link from "next/link";
import { Detection } from "@/lib/types";
import { formatInr, formatScore } from "@/lib/format";
import { DecisionBadge } from "@/components/Badge";

export function ExplainPanel({ d }: { d: Detection | null }) {
  if (!d) {
    return (
      <div className="rounded-lg border border-border bg-surface p-5 text-sm text-text-muted">
        Click a detection row to see why it was flagged.
      </div>
    );
  }

  const rows: [string, React.ReactNode][] = [
    ["Entity", <span key="e" className="font-mono text-xs break-all">{d.entity_id}</span>],
    ["Amount", formatInr(d.TransactionAmt)],
    [
      "Population score",
      <span key="p">
        <span className="font-mono font-semibold">{formatScore(d.score_population)}</span>{" "}
        <span className="text-text-faint">drives the decision (ADR-0007)</span>
      </span>,
    ],
    [
      "Entity-deviation score",
      <span key="ed" className="text-text-muted">
        <span className="font-mono">{formatScore(d.score_entity_deviation)}</span>{" "}
        <span className="text-text-faint">transparency only, not used</span>
      </span>,
    ],
    [
      "Combined score",
      <span key="c" className="text-text-muted">
        <span className="font-mono">{formatScore(d.score_combined)}</span>{" "}
        <span className="text-text-faint">transparency only, not used</span>
      </span>,
    ],
    ["Typology tag", d.typology_tag ?? <span className="text-text-faint">none</span>],
    [
      "Ring cluster",
      d.ring_cluster_id ? (
        <Link href={`/demo/ring/${d.ring_cluster_id}`} className="text-accent hover:underline">
          {d.ring_cluster_id}
        </Link>
      ) : (
        <span className="text-text-faint">none</span>
      ),
    ],
    ["Decision", <DecisionBadge key="d" decision={d.decision} />],
    ["Reasoning", d.decision_reasoning],
    [
      "Ground truth",
      d.ground_truth_fraud === null ? (
        <span className="text-text-faint">no ground truth (synthetic demo data)</span>
      ) : (
        <span>
          {d.ground_truth_fraud === 1 ? "fraud" : "benign"}{" "}
          <span className="text-text-faint">(evaluation only, the detector never sees this)</span>
        </span>
      ),
    ],
  ];

  return (
    <div className="rounded-lg border border-border bg-surface p-5 sticky top-20">
      <h3 className="font-semibold mb-3 font-mono text-sm">Detection {d.TransactionID}</h3>
      <dl className="space-y-2.5 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4">
            <dt className="text-text-muted shrink-0">{label}</dt>
            <dd className="text-right">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
