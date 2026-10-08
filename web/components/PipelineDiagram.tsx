function Box({
  title,
  detail,
  tone = "default",
}: {
  title: string;
  detail?: string;
  tone?: "default" | "accent" | "muted";
}) {
  const toneClasses = {
    default: "border-border bg-surface",
    accent: "border-accent/40 bg-accent/10",
    muted: "border-border bg-surface/50",
  }[tone];
  return (
    <div className={`rounded-md border px-3 py-2.5 text-center ${toneClasses}`}>
      <div className="text-xs font-medium text-text leading-tight">{title}</div>
      {detail && <div className="text-[11px] text-text-muted mt-0.5 leading-tight">{detail}</div>}
    </div>
  );
}

function Arrow({ vertical = false }: { vertical?: boolean }) {
  return (
    <div className={`flex items-center justify-center text-text-faint ${vertical ? "h-5" : "w-5"}`}>
      {vertical ? "↓" : "→"}
    </div>
  );
}

export function PipelineDiagram() {
  return (
    <div className="rounded-lg border border-border bg-surface/50 p-6 overflow-x-auto">
      <div className="flex flex-col items-center gap-1 min-w-[640px]">
        <Box title="IEEE-CIS transactions" detail="590K rows, real Kaggle data" />
        <Arrow vertical />
        <Box title="Entity reconstruction" detail="card + address + D1 fingerprint" />
        <Arrow vertical />
        <Box title="Entity-level, time-based split" detail="train / val / test, never random" />
        <Arrow vertical />
        <Box title="Feature pipeline" detail="fit on train only" />
        <Arrow vertical />
        <div className="flex gap-4 items-start">
          <Box title="IsolationForest" detail="population-only" tone="accent" />
          <Box title="IsolationForest" detail="population + entity-deviation" tone="muted" />
          <Box title="Ring detection" detail="shared-device graph" tone="accent" />
          <Box title="Typology tagger" detail="explanation only" tone="muted" />
        </div>
        <Arrow vertical />
        <Box title="Orchestrator" detail="allow / review / decline, ADR-0007" tone="accent" />
        <Arrow vertical />
        <div className="flex gap-4">
          <Box title="Audit log" detail="every decision, no exceptions" />
          <Box title="Results store" detail="read by the console" />
        </div>
        <Arrow vertical />
        <Box title="Risk Console" detail="FastAPI + HTMX, 5 features" />
      </div>
    </div>
  );
}
