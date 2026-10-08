import { Decision, Source } from "@/lib/types";

const decisionStyles: Record<Decision, string> = {
  allow: "bg-blue-bg text-blue",
  review: "bg-amber-bg text-amber",
  decline: "bg-red-bg text-red",
};

const sourceStyles: Record<Source, string> = {
  benchmark: "bg-green-bg text-green",
  demo: "bg-amber-bg text-amber",
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

export function SourceBadge({ source }: { source: Source }) {
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-medium tracking-wide ${sourceStyles[source]}`}
    >
      {source}
    </span>
  );
}
