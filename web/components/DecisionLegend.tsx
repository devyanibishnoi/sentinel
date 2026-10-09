import { DecisionBadge } from "@/components/Badge";

export function DecisionLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-text-muted mb-5">
      <span className="flex items-center gap-2">
        <DecisionBadge decision="decline" /> auto-declined, no human involved
      </span>
      <span className="flex items-center gap-2">
        <DecisionBadge decision="review" /> routed to a human, confidence was high but exposure wasn&apos;t
      </span>
      <span className="flex items-center gap-2">
        <DecisionBadge decision="allow" /> nothing triggered, still logged
      </span>
    </div>
  );
}
