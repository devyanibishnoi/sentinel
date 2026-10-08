import { Source } from "@/lib/types";

export function SourceToggle({
  source,
  onChange,
}: {
  source: Source;
  onChange: (s: Source) => void;
}) {
  return (
    <div className="inline-flex rounded-md border border-border overflow-hidden mb-5">
      {(["benchmark", "demo"] as const).map((s) => (
        <button
          key={s}
          onClick={() => onChange(s)}
          className={`px-4 py-1.5 text-sm capitalize transition-colors ${
            source === s ? "bg-surface-raised text-text" : "bg-surface text-text-muted hover:text-text"
          }`}
        >
          {s}
        </button>
      ))}
    </div>
  );
}
