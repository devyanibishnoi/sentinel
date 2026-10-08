export function Caveat({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-amber/30 bg-amber-bg/60 px-4 py-3 text-sm text-amber/90 mb-6">
      {children}
    </div>
  );
}
