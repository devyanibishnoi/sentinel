"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { GITHUB_REPO_URL } from "@/lib/site";

const links = [
  { href: "/demo", label: "Detection Feed" },
  { href: "/demo/metrics", label: "Metrics" },
  { href: "/demo/ring", label: "Ring Viewer" },
  { href: "/demo/audit", label: "Audit Trail" },
];

export function DemoNav() {
  const pathname = usePathname();
  return (
    <header className="border-b border-border bg-surface/80 backdrop-blur sticky top-0 z-20">
      <div className="mx-auto max-w-6xl px-6 flex items-center justify-between h-14">
        <div className="flex items-center gap-6">
          <Link href="/" className="font-semibold tracking-tight text-text hover:text-accent transition-colors">
            Sentinel
          </Link>
          <nav className="flex gap-1">
            {links.map((l) => {
              const active = l.href === "/demo" ? pathname === "/demo" : pathname.startsWith(l.href);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                    active ? "bg-surface-raised text-text" : "text-text-muted hover:text-text"
                  }`}
                >
                  {l.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <a
          href={GITHUB_REPO_URL}
          target="_blank"
          rel="noreferrer"
          className="text-sm text-text-muted hover:text-text transition-colors"
        >
          View source ↗
        </a>
      </div>
    </header>
  );
}
