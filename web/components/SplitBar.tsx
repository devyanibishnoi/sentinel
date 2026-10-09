export function SplitBar({
  segments,
}: {
  segments: { label: string; value: number; emphasis?: boolean }[];
}) {
  return (
    <div>
      <div className="h-7 rounded-sm overflow-hidden flex gap-0.5">
        {segments.map((s) => (
          <div
            key={s.label}
            className={s.emphasis ? "bg-accent" : "bg-chart-track"}
            style={{ width: `${s.value * 100}%` }}
          />
        ))}
      </div>
      <div className="flex gap-5 mt-2.5 text-xs text-text-muted">
        {segments.map((s) => (
          <span key={s.label} className="flex items-center gap-1.5">
            <span
              className={`inline-block w-2.5 h-2.5 rounded-full ${s.emphasis ? "bg-accent" : "bg-chart-track"}`}
            />
            <span className={s.emphasis ? "text-text" : ""}>{s.label}</span>
            <span className="font-mono tabular-nums">{(s.value * 100).toFixed(0)}%</span>
          </span>
        ))}
      </div>
    </div>
  );
}
