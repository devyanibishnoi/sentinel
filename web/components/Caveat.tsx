export function Caveat({
  children,
  tone = "info",
}: {
  children: React.ReactNode;
  tone?: "info" | "warning";
}) {
  if (tone === "warning") {
    return (
      <div className="rounded-md border border-border bg-surface border-l-2 border-l-amber pl-4 pr-4 py-3 text-sm text-text-muted mb-6">
        {children}
      </div>
    );
  }
  return (
    <div className="rounded-md border border-border bg-surface px-4 py-3 text-sm text-text-muted mb-6">
      {children}
    </div>
  );
}
