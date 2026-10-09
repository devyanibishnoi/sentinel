interface BarDatum {
  label: string;
  value: number;
  emphasis?: boolean;
}

export function BarChart({
  data,
  valueFormat = (v: number) => v.toFixed(3),
}: {
  data: BarDatum[];
  valueFormat?: (v: number) => string;
}) {
  const max = Math.max(...data.map((d) => d.value));

  return (
    <div className="space-y-3">
      {data.map((d) => {
        const widthPct = Math.max(2, (d.value / max) * 100);
        return (
          <div key={d.label} className="flex items-center gap-3">
            <div
              className={`w-64 sm:w-72 text-sm shrink-0 truncate text-right ${
                d.emphasis ? "text-text font-medium" : "text-text-muted"
              }`}
            >
              {d.label}
            </div>
            <div className="flex-1 h-6 flex items-center">
              <div
                className={`h-4 rounded-r-sm ${d.emphasis ? "bg-accent" : "bg-chart-track"}`}
                style={{ width: `${widthPct}%` }}
              />
            </div>
            <div
              className={`w-20 text-sm font-mono tabular-nums shrink-0 ${
                d.emphasis ? "text-accent font-medium" : "text-text-muted"
              }`}
            >
              {valueFormat(d.value)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
