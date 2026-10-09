export function StatTile({
  value,
  label,
  accent = false,
  clickable = false,
}: {
  value: string;
  label: string;
  accent?: boolean;
  clickable?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border border-border bg-surface p-5 h-full transition-colors ${
        clickable ? "hover:border-border-strong hover:bg-surface-raised" : ""
      }`}
    >
      <div className={`text-3xl font-semibold font-mono ${accent ? "text-accent" : "text-text"}`}>{value}</div>
      <div className="text-sm text-text-muted mt-1.5 leading-snug">{label}</div>
    </div>
  );
}
