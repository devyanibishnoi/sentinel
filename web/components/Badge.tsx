import { Decision, Source } from "@/lib/types";

const decisionStyles: Record<Decision, string> = {
  allow: "border border-border-strong text-text-muted",
  review: "bg-amber-bg text-amber",
  decline: "bg-red-bg text-red",
};

export function DecisionBadge({ decision }: { decision: Decision }) {
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-medium tracking-wide ${decisionStyles[decision]}`}
    >
      {decision}
    </span>
  );
}

// Deliberately NOT reusing decision colors (red/amber) here: source and
// decision are two different axes of meaning, giving them the same
// color vocabulary made both harder to read at a glance, not easier.
export function SourceBadge({ source }: { source: Source }) {
  if (source === "benchmark") {
    return (
      <span className="inline-block rounded px-2 py-0.5 text-xs font-medium tracking-wide bg-accent-bg text-accent">
        benchmark
      </span>
    );
  }
  return (
    <span className="inline-block rounded px-2 py-0.5 text-xs font-medium tracking-wide border border-dashed border-border-strong text-text-muted">
      demo
    </span>
  );
}
