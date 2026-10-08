export function StatTile({
  value,
  label,
  accent = false,
}: {
  value: string;
  label: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-5">
      <div className={`text-3xl font-semibold font-mono ${accent ? "text-accent" : "text-text"}`}>{value}</div>
      <div className="text-sm text-text-muted mt-1.5 leading-snug">{label}</div>
    </div>
  );
}
